from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException

from commerce_platform.platform.config.merge import load_merged_platform_config
from commerce_platform.platform.store.repos import CatalogRepo, TrackingRepo, UserRepo
from commerce_platform.web.config import WebConfig
from commerce_platform.web.deps import (
    get_catalog_repo,
    get_config_path,
    get_config_repo,
    get_deal_repo,
    get_tracking_repo,
    get_user_repo,
    get_web_config,
    require_admin,
)
from commerce_platform.web.retailers import detect_retailer_and_asin
from commerce_platform.web.schemas import (
    AdminProductPatchBody,
    AdminIngestionConfigPatchBody,
    AdminWatchCreateBody,
    AdminWatchPatchBody,
    ApproveBody,
    ListingPreviewResponse,
    RejectBody,
    WatchResponse,
)
from commerce_platform.web.listing_scrape import scrape_listing
from commerce_platform.web.slug_suggest import suggest_product_id_from_title
from commerce_platform.web.validators import slug_ok

router = APIRouter(prefix="/admin", tags=["admin"])


def _load_config_dict(config_path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise HTTPException(500, "Invalid config file format")
    return raw


def _write_config_dict(config_path: Path, payload: dict[str, Any]) -> None:
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


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


@router.get("/requests/{request_id}/listing-preview", response_model=ListingPreviewResponse)
async def admin_listing_preview(
    request_id: int,
    _admin=Depends(require_admin),
    tracking_repo: TrackingRepo = Depends(get_tracking_repo),
    config_path: Path = Depends(get_config_path),
):
    """Fetch the retailer listing and suggest slug, name, brand, image, and price."""
    req = await tracking_repo.get(request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    scraped = await scrape_listing(req.raw_url, config_path=config_path, label=f"admin_preview_{request_id}")
    if not scraped.ok:
        return {
            "ok": False,
            "retailer": scraped.retailer,
            "reason": scraped.reason,
            "asin": scraped.asin,
            "fetch_url": scraped.fetch_url,
            "suggested_product_id": None,
            "name": req.desired_product_name,
            "brand": None,
            "image_url": None,
            "price_inr": None,
            "mrp_inr": None,
            "in_stock": None,
        }

    name = (scraped.name or (req.desired_product_name or "").strip()).strip()
    suggested = suggest_product_id_from_title(name) if name else None

    return {
        "ok": True,
        "retailer": scraped.retailer,
        "asin": scraped.asin,
        "fetch_url": scraped.fetch_url,
        "suggested_product_id": suggested,
        "name": name or None,
        "brand": scraped.brand,
        "image_url": scraped.image_url,
        "price_inr": scraped.price_inr,
        "mrp_inr": scraped.mrp_inr,
        "in_stock": scraped.in_stock,
    }


@router.post("/requests/{request_id}/approve")
async def admin_approve(
    request_id: int,
    body: ApproveBody,
    admin=Depends(require_admin),
    tracking_repo: TrackingRepo = Depends(get_tracking_repo),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    if not slug_ok(body.product_id.lower()):
        raise HTTPException(400, "product_id must be alphanumeric with optional _ -")
    pid = body.product_id.lower()
    req = await tracking_repo.get(request_id)
    if not req or req.status != "pending":
        raise HTTPException(404, "Request not found or not pending")
    scraped = await scrape_listing(req.raw_url, config_path=config_path, label=f"admin_approve_{request_id}")
    retailer = scraped.retailer
    asin = scraped.asin
    if not retailer:
        raise HTTPException(400, "Stored URL has no supported retailer")
    name = body.name.strip() or (scraped.name or "").strip()
    if not name:
        raise HTTPException(400, "name is required")
    brand = body.brand.strip() if body.brand and body.brand.strip() else scraped.brand
    image_url = body.image_url.strip() if body.image_url and body.image_url.strip() else scraped.image_url
    await catalog_repo.ensure_product_and_add_watch(
        product_id=pid,
        name=name,
        brand=brand,
        category=body.category,
        source=retailer,
        url=req.raw_url.strip(),
        asin=asin,
        affiliate_tag=body.affiliate_tag if retailer == "amazon" else None,
        poll_seconds=body.poll_seconds,
        source_request_id=request_id,
        image_url=image_url,
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
                "has_catalog_row": p.id in ids,
                "watches": watches,
            }
        )

    return {"config_path": str(config_path.resolve()), "products": products_out}


@router.get("/ingestion-config")
async def admin_ingestion_config(
    _admin=Depends(require_admin),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    """YAML-backed deal ingestors (`platform_sources`) and defaults."""
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    return {
        "config_path": str(config_path.resolve()),
        "config_reload_seconds": cfg.platform.config_reload_seconds,
        "defaults_poll_seconds": cfg.defaults.poll_seconds,
        "platform_sources": [s.model_dump(mode="json") for s in cfg.platform_sources],
    }


@router.patch("/ingestion-config")
async def admin_patch_ingestion_config(
    body: AdminIngestionConfigPatchBody,
    _admin=Depends(require_admin),
    config_path: Path = Depends(get_config_path),
):
    raw = _load_config_dict(config_path)

    platform_obj = raw.get("platform")
    if not isinstance(platform_obj, dict):
        platform_obj = {}
        raw["platform"] = platform_obj
    defaults_obj = raw.get("defaults")
    if not isinstance(defaults_obj, dict):
        defaults_obj = {}
        raw["defaults"] = defaults_obj

    platform_sources_raw = raw.get("platform_sources")
    if platform_sources_raw is None:
        platform_sources_raw = []
        raw["platform_sources"] = platform_sources_raw
    if not isinstance(platform_sources_raw, list):
        raise HTTPException(400, "platform_sources must be a list in config")

    platform_obj["config_reload_seconds"] = body.config_reload_seconds
    defaults_obj["poll_seconds"] = body.defaults_poll_seconds

    updates: dict[tuple[str, int], int] = {}
    incoming_by_type: dict[str, int] = {}
    for src in body.platform_sources:
        ordinal = incoming_by_type.get(src.type, 0)
        incoming_by_type[src.type] = ordinal + 1
        updates[(src.type, ordinal)] = src.poll_seconds
    seen_by_type: dict[str, int] = {}
    for idx, src in enumerate(platform_sources_raw):
        if not isinstance(src, dict):
            continue
        src_type = src.get("type")
        if not isinstance(src_type, str):
            continue
        ordinal = seen_by_type.get(src_type, 0)
        key = (src_type, ordinal)
        seen_by_type[src_type] = ordinal + 1
        if key in updates:
            src["poll_seconds"] = updates[key]

    _write_config_dict(config_path, raw)
    return {"ok": True}


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


# --- Deal Configuration Routes ---


@router.get("/deals/config")
async def admin_get_deals_config(
    _admin=Depends(require_admin),
    config_repo: Any = Depends(get_config_repo),
):
    """Get deal scoring configuration."""
    from commerce_platform.platform.config.schema import ScoringWeightsConfig

    threshold = await config_repo.get("deals.scoring.threshold", 0.40)
    cooldown = await config_repo.get("deals.scoring.repost_cooldown_hours", 24)
    weights = await config_repo.get_all_prefixed("deals.scoring.weights.")

    if not weights:
        defaults = ScoringWeightsConfig()
        weights = {
            "deals.scoring.weights.lowest_90d": defaults.lowest_90d,
            "deals.scoring.weights.below_30d_median": defaults.below_30d_median,
            "deals.scoring.weights.discount_vs_mrp": defaults.discount_vs_mrp,
            "deals.scoring.weights.cross_retailer_best": defaults.cross_retailer_best,
            "deals.scoring.weights.has_offers": defaults.has_offers,
            "deals.scoring.weights.aggregator_corroborated": defaults.aggregator_corroborated,
        }

    return {"threshold": threshold, "repost_cooldown_hours": cooldown, "weights": weights}


@router.patch("/deals/config")
async def admin_patch_deals_config(
    body: DealsScoringConfigBody,
    _admin=Depends(require_admin),
    config_repo: Any = Depends(get_config_repo),
):
    """Update deal scoring configuration."""
    await config_repo.set("deals.scoring.threshold", body.threshold)
    await config_repo.set("deals.scoring.repost_cooldown_hours", body.repost_cooldown_hours)

    for key, value in body.weights.items():
        await config_repo.set(f"deals.scoring.weights.{key}", value)

    return {"ok": True}


@router.get("/deals/live")
async def admin_get_live_deals(
    limit: int = 50,
    offset: int = 0,
    _admin=Depends(require_admin),
    deal_repo: Any = Depends(get_deal_repo),
):
    """Get currently active deals."""
    deals = await deal_repo.list_active(limit=limit, offset=offset)

    return [
        DealCardResponse(
            id=deal.id or 0,
            product_url=deal.product_url,
            product_id=deal.product_id,
            retailer=deal.retailer,
            price_inr=deal.price_paise / 100 if deal.price_paise else 0,
            mrp_inr=deal.mrp_paise / 100 if deal.mrp_paise else None,
            discount_pct=deal.discount_pct,
            score=deal.score,
            score_reasons=deal.score_reasons,
            product_title=deal.product_title,
            image_url=deal.image_url,
            source=deal.source,
            is_active=deal.is_active,
            first_seen_at=deal.first_seen_at,
            last_confirmed_at=deal.last_confirmed_at,
        )
        for deal in deals
    ]


@router.get("/deals/history")
async def admin_get_deal_history(
    product_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _admin=Depends(require_admin),
    deal_repo: Any = Depends(get_deal_repo),
):
    """Get expired deals (deal history)."""
    deals = await deal_repo.list_expired(product_id=product_id, limit=limit, offset=offset)

    return [
        DealCardResponse(
            id=deal.id or 0,
            product_url=deal.product_url,
            product_id=deal.product_id,
            retailer=deal.retailer,
            price_inr=deal.price_paise / 100 if deal.price_paise else 0,
            mrp_inr=deal.mrp_paise / 100 if deal.mrp_paise else None,
            discount_pct=deal.discount_pct,
            score=deal.score,
            score_reasons=deal.score_reasons,
            product_title=deal.product_title,
            image_url=deal.image_url,
            source=deal.source,
            is_active=deal.is_active,
            first_seen_at=deal.first_seen_at,
            last_confirmed_at=deal.last_confirmed_at,
        )
        for deal in deals
    ]


@router.get("/deals/pending")
async def admin_get_pending_approval(
    minutes: int = 5,
    limit: int = 50,
    offset: int = 0,
    _admin=Depends(require_admin),
    deal_repo: Any = Depends(get_deal_repo),
):
    """Get deals pending admin approval."""
    deals = await deal_repo.get_pending_approval(minutes=minutes)

    return [
        DealCardResponse(
            id=deal.id or 0,
            product_url=deal.product_url,
            product_id=deal.product_id,
            retailer=deal.retailer,
            price_inr=deal.price_paise / 100 if deal.price_paise else 0,
            mrp_inr=deal.mrp_paise / 100 if deal.mrp_paise else None,
            discount_pct=deal.discount_pct,
            score=deal.score,
            score_reasons=deal.score_reasons,
            product_title=deal.product_title,
            image_url=deal.image_url,
            source=deal.source,
            is_active=deal.is_active,
            first_seen_at=deal.first_seen_at,
            last_confirmed_at=deal.last_confirmed_at,
        )
        for deal in deals[offset : offset + limit]  # Client-side pagination
    ]


@router.post("/deals/{deal_id}/approve")
async def admin_approve_deal(
    deal_id: int,
    note: str | None = None,
    _admin=Depends(require_admin),
    user: Any = Depends(get_user_repo),  # Get current user from auth context
    deal_repo: Any = Depends(get_deal_repo),
):
    """Admin approves a deal for notification to users."""
    deal = await deal_repo.get_by_id(deal_id)
    if not deal:
        raise HTTPException(404, f"Deal {deal_id} not found")

    # Mark as approved
    user_id = getattr(user, "id", None) if hasattr(user, "id") else None
    await deal_repo.mark_reviewed(deal_id, "approved", user_id=user_id, reason=note)

    return {"ok": True, "deal_id": deal_id, "status": "approved"}


@router.post("/deals/{deal_id}/reject")
async def admin_reject_deal(
    deal_id: int,
    reason: str | None = None,
    _admin=Depends(require_admin),
    user: Any = Depends(get_user_repo),
    deal_repo: Any = Depends(get_deal_repo),
):
    """Admin rejects a deal with optional reason."""
    deal = await deal_repo.get_by_id(deal_id)
    if not deal:
        raise HTTPException(404, f"Deal {deal_id} not found")

    # Mark as rejected
    user_id = getattr(user, "id", None) if hasattr(user, "id") else None
    await deal_repo.mark_reviewed(deal_id, "rejected", user_id=user_id, reason=reason)

    return {"ok": True, "deal_id": deal_id, "status": "rejected", "reason": reason}
