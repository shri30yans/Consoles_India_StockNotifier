"""Public deals API — serve active deals for frontend discovery page."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from commerce_platform.web.deps import get_deal_repo
from commerce_platform.web.schemas import DealCardResponse

router = APIRouter()


@router.get("/deals")
async def get_active_deals(
    retailer: str | None = Query(None, description="Filter by retailer"),
    min_discount: float | None = Query(None, description="Minimum discount percentage"),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    deal_repo: Any = Depends(get_deal_repo),
):
    """Get active deals, optionally filtered by retailer/discount."""
    deals = await deal_repo.list_active(
        retailer=retailer,
        min_discount=min_discount,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )

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
async def get_deal_history(
    product_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    deal_repo: Any = Depends(get_deal_repo),
):
    """Get expired deals (deal history) for a product."""
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
