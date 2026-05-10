"""Public deals API — serve active deals for frontend discovery page."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from commerce_platform.web.deal_card import deal_to_card_response
from commerce_platform.web.deps import get_deal_repo

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

    return [deal_to_card_response(deal) for deal in deals]


@router.get("/deals/history")
async def get_deal_history(
    product_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    deal_repo: Any = Depends(get_deal_repo),
):
    """Get expired deals (deal history) for a product."""
    deals = await deal_repo.list_expired(product_id=product_id, limit=limit, offset=offset)

    return [deal_to_card_response(deal) for deal in deals]
