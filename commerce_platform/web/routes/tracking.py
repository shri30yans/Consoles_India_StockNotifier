from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from commerce_platform.platform.store.repos import TrackingRepo
from commerce_platform.web.deps import get_tracking_repo, require_user
from commerce_platform.web.retailers import detect_retailer_and_asin, validate_public_product_url
from commerce_platform.web.schemas import TrackingRequestBody

router = APIRouter(tags=["tracking"])


@router.post("/requests")
async def submit_request(
    request: Request,
    body: TrackingRequestBody,
    user=Depends(require_user),
    tracking_repo: TrackingRepo = Depends(get_tracking_repo),
):
    ip = request.client.host if request.client else "unknown"
    if not request.app.state.rate_limiter.allow(f"ip:{ip}"):
        raise HTTPException(429, "Too many requests; try later")
    ok, err = validate_public_product_url(body.url)
    if not ok:
        raise HTTPException(400, err or "Invalid URL")
    retailer, _asin = detect_retailer_and_asin(body.url)
    if not retailer:
        raise HTTPException(400, "Could not detect supported retailer")
    rid = await tracking_repo.create(
        user_id=user.id,
        raw_url=body.url,
        retailer_hint=retailer,
        desired_product_name=body.desired_product_name,
        note=body.note,
    )
    return {"id": rid, "status": "pending"}


@router.get("/me/requests")
async def my_requests(user=Depends(require_user), tracking_repo: TrackingRepo = Depends(get_tracking_repo)):
    items = await tracking_repo.list_for_user(user.id)
    return [
        {
            "id": r.id,
            "raw_url": r.raw_url,
            "status": r.status,
            "retailer_hint": r.normalized_retailer_hint,
            "desired_product_name": r.desired_product_name,
            "created_at": r.created_at,
            "admin_note": r.admin_note,
            "promoted_product_id": r.promoted_product_id,
        }
        for r in items
    ]
