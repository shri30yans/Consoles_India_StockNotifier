"""Canonical mapping from DB deal rows to API card responses."""

from __future__ import annotations

from commerce_platform.platform.store.repos.deal_repo import DealRow
from commerce_platform.web.schemas import DealCardResponse


def deal_to_card_response(deal: DealRow) -> DealCardResponse:
    """Canonical paise→INR conversion for HTTP responses."""
    return DealCardResponse(
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
