"""Tracking-request admin endpoints (list / preview / approve / reject)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException

from commerce_platform.platform.store.repos import CatalogRepo, TrackingRepo
from commerce_platform.stock.listing_preview import scrape_listing
from commerce_platform.web.deps import (
    get_catalog_repo,
    get_config_path,
    get_tracking_repo,
    require_admin,
)
from commerce_platform.web.schemas import (
    ApproveBody,
    ListingPreviewResponse,
    RejectBody,
)
from commerce_platform.web.slug_suggest import suggest_product_id_from_title
from commerce_platform.web.validators import slug_ok

router = APIRouter()


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
        for r in await tracking_repo.list_by_status(
            cast(Literal["pending", "approved", "rejected"] | None, status)
        )
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
    scraped = await scrape_listing(
        req.raw_url, config_path=config_path, label=f"admin_preview_{request_id}"
    )
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
    scraped = await scrape_listing(
        req.raw_url, config_path=config_path, label=f"admin_approve_{request_id}"
    )
    retailer = scraped.retailer
    asin = scraped.asin
    if not retailer:
        raise HTTPException(400, "Stored URL has no supported retailer")
    name = body.name.strip() or (scraped.name or "").strip()
    if not name:
        raise HTTPException(400, "name is required")
    brand = body.brand.strip() if body.brand and body.brand.strip() else scraped.brand
    image_url = (
        body.image_url.strip() if body.image_url and body.image_url.strip() else scraped.image_url
    )
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
    await tracking_repo.resolve(
        request_id,
        decision="approved",
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
    await tracking_repo.resolve(
        request_id,
        decision="rejected",
        admin_id=admin.id,
        admin_note=body.admin_note,
    )
    return {"ok": True}
