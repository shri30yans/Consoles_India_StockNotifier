"""Product catalog and watch management admin endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from commerce_platform.platform.config.merge import load_merged_platform_config
from commerce_platform.platform.store.repos import CatalogRepo
from commerce_platform.web.deps import (
    get_catalog_repo,
    get_config_path,
    require_admin,
)
from commerce_platform.web.schemas import (
    AdminApplyPollAllBody,
    AdminProductPatchBody,
    AdminWatchCreateBody,
    AdminWatchPatchBody,
    WatchResponse,
)
from commerce_platform.web.validators import slug_ok

router = APIRouter()


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
                    db_watch_id=row.db_watch_id if row else None,
                )
            )
        products_out.append(
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "colour": p.colour,
                "image_url": p.image_url,
                "watches": watches,
            }
        )

    return {
        "defaults_poll_seconds": cfg.defaults.poll_seconds,
        "products": products_out,
    }


@router.post("/catalog/watches/poll-all")
async def admin_apply_poll_all_listings(
    body: AdminApplyPollAllBody,
    _admin=Depends(require_admin),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
):
    """Set every tracked listing (all products × retailers) to the same poll interval."""
    n = await catalog_repo.set_poll_seconds_on_all_watches(body.poll_seconds)
    return {"ok": True, "updated": n}


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


@router.post("/catalog/products/{product_id}/watches/override")
async def admin_upsert_watch_override(
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
            colour=p.colour,
            image_url=p.image_url,
        )
    wid = await catalog_repo.upsert_watch_by_product_url(
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
