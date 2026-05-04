from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from commerce_platform.platform.config.merge import load_merged_platform_config
from commerce_platform.platform.store.repos import CatalogRepo, TrackingRepo, UserRepo
from commerce_platform.web.config import WebConfig
from commerce_platform.web.deps import (
    get_catalog_repo,
    get_config_path,
    get_tracking_repo,
    get_user_repo,
    get_web_config,
    require_admin,
)
from commerce_platform.web.retailers import detect_retailer_and_asin
from commerce_platform.web.schemas import (
    AdminProductPatchBody,
    AdminWatchCreateBody,
    AdminWatchPatchBody,
    ApproveBody,
    RejectBody,
    WatchResponse,
)
from commerce_platform.web.validators import slug_ok

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/requests")
async def admin_list(
    status: str | None = None,
    _admin=Depends(require_admin),
    tracking_repo: TrackingRepo = Depends(get_tracking_repo),
):
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "raw_url": r.raw_url,
            "normalized_retailer_hint": r.normalized_retailer_hint,
            "desired_product_name": r.desired_product_name,
            "note": r.note,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in await tracking_repo.list_by_status(status)
    ]


@router.post("/requests/{request_id}/approve")
async def admin_approve(
    request_id: int,
    body: ApproveBody,
    admin=Depends(require_admin),
    tracking_repo: TrackingRepo = Depends(get_tracking_repo),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
):
    if not slug_ok(body.product_id.lower()):
        raise HTTPException(400, "product_id must be alphanumeric with optional _ -")
    pid = body.product_id.lower()
    req = await tracking_repo.get(request_id)
    if not req or req.status != "pending":
        raise HTTPException(404, "Request not found or not pending")
    retailer, asin = detect_retailer_and_asin(req.raw_url)
    if not retailer:
        raise HTTPException(400, "Stored URL has no supported retailer")
    await catalog_repo.ensure_product_and_add_watch(
        product_id=pid,
        name=body.name,
        brand=body.brand,
        category=body.category,
        source=retailer,
        url=req.raw_url.strip(),
        asin=asin,
        affiliate_tag=body.affiliate_tag if retailer == "amazon" else None,
        poll_seconds=body.poll_seconds,
        source_request_id=request_id,
        image_url=body.image_url,
    )
    await tracking_repo.set_approved_and_promote(
        request_id,
        admin_id=admin.id,
        admin_note=None,
        promoted_product_id=pid,
    )
    return {"ok": True, "promoted_product_id": pid}


@router.post("/requests/{request_id}/reject")
async def admin_reject(
    request_id: int,
    body: RejectBody,
    admin=Depends(require_admin),
    tracking_repo: TrackingRepo = Depends(get_tracking_repo),
):
    req = await tracking_repo.get(request_id)
    if not req or req.status != "pending":
        raise HTTPException(404, "Request not found or not pending")
    await tracking_repo.set_rejected(request_id, admin_id=admin.id, admin_note=body.admin_note)
    return {"ok": True}


@router.get("/settings/auth")
async def admin_auth_settings(
    _admin=Depends(require_admin),
    user_repo: UserRepo = Depends(get_user_repo),
    config_path: Path = Depends(get_config_path),
    web: WebConfig = Depends(get_web_config),
):
    user_count = await user_repo.count()
    return {
        "config_path": str(config_path.resolve()),
        "jwt_algorithm": web.jwt_alg,
        "jwt_expire_seconds": web.jwt_expire_seconds,
        "open_registration": web.open_registration,
        "bootstrap_admin_env_configured": bool(web.bootstrap_admin_email and web.bootstrap_admin_password),
        "requests_per_hour_per_ip": web.web_requests_per_hour_per_ip,
        "cors_origins": ",".join(web.cors_origins),
        "using_default_jwt_secret": web.jwt_secret == "dev-insecure-change-me",
        "registered_users": user_count,
        "note": "WEB_JWT_SECRET and password values are never returned. Use the same PLATFORM_CONFIG for every process that touches this database.",
    }


@router.get("/catalog")
async def admin_catalog(
    _admin=Depends(require_admin),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    ids = await catalog_repo.list_product_ids()
    db_watches_by_product: dict[str, list[WatchResponse]] = {}
    for pid in ids:
        watches = await catalog_repo.list_watches_for_product(pid)
        db_watches_by_product[pid] = [
            WatchResponse(
                source=w.source,
                url=w.url,
                asin=w.asin,
                affiliate_tag=w.affiliate_tag,
                poll_seconds=w.poll_seconds,
                db_watch_id=w.id,
            )
            for w in watches
        ]

    products_out: list[dict[str, Any]] = []
    for p in cfg.products:
        dbw = db_watches_by_product.get(p.id, [])
        by_url = {w.url: w for w in dbw}
        watches: list[WatchResponse] = []
        for w in p.watches:
            row = by_url.get(w.url)
            watches.append(
                WatchResponse(
                    source=w.source,
                    url=w.url,
                    asin=w.asin,
                    affiliate_tag=w.affiliate_tag,
                    poll_seconds=w.poll_seconds,
                    db_watch_id=row.id if row else None,
                )
            )
        products_out.append(
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "emoji": p.emoji,
                "colour": p.colour,
                "image_url": p.image_url,
                "has_catalog_row": p.id in ids,
                "watches": watches,
            }
        )

    return {"config_path": str(config_path.resolve()), "products": products_out}


@router.patch("/catalog/products/{product_id}")
async def admin_patch_catalog_product(
    product_id: str,
    body: AdminProductPatchBody,
    _admin=Depends(require_admin),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    pid = product_id.lower()
    if not slug_ok(pid):
        raise HTTPException(400, "invalid product id")
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    if not any(x.id == pid for x in cfg.products):
        raise HTTPException(404, "Unknown product")
    await catalog_repo.upsert_product(
        product_id=pid,
        name=body.name,
        brand=body.brand,
        category=body.category,
        emoji=body.emoji,
        colour=body.colour,
        image_url=body.image_url,
    )
    return {"ok": True}


@router.post("/catalog/products/{product_id}/watches")
async def admin_add_watch(
    product_id: str,
    body: AdminWatchCreateBody,
    _admin=Depends(require_admin),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    pid = product_id.lower()
    if not slug_ok(pid):
        raise HTTPException(400, "invalid product id")
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    p = next((x for x in cfg.products if x.id == pid), None)
    if not p:
        raise HTTPException(404, "Unknown product")
    ids = await catalog_repo.list_product_ids()
    if pid not in ids:
        await catalog_repo.upsert_product(
            product_id=pid,
            name=p.name,
            brand=p.brand,
            category=p.category,
            emoji=p.emoji,
            colour=p.colour,
            image_url=p.image_url,
        )
    wid = await catalog_repo.insert_watch(
        product_id=pid,
        source=body.source,
        url=body.url,
        asin=body.asin,
        affiliate_tag=body.affiliate_tag,
        poll_seconds=body.poll_seconds,
    )
    return {"ok": True, "watch_id": wid}


@router.patch("/catalog/watches/{watch_id}")
async def admin_patch_watch(
    watch_id: int,
    body: AdminWatchPatchBody,
    _admin=Depends(require_admin),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
):
    if not await catalog_repo.update_watch(
        watch_id,
        source=body.source,
        url=body.url,
        asin=body.asin,
        affiliate_tag=body.affiliate_tag,
        poll_seconds=body.poll_seconds,
    ):
        raise HTTPException(404, "Watch not found")
    return {"ok": True}


@router.delete("/catalog/watches/{watch_id}")
async def admin_delete_watch(
    watch_id: int,
    _admin=Depends(require_admin),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
):
    if not await catalog_repo.delete_watch(watch_id):
        raise HTTPException(404, "Watch not found")
    return {"ok": True}
