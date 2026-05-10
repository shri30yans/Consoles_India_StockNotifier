"""Deal review admin endpoints (config / live / history / approve / reject)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from commerce_platform.platform.store.repos import DealRepo
from commerce_platform.web.deal_card import deal_to_card_response
from commerce_platform.web.deps import (
    get_config_repo,
    get_deal_repo,
    require_admin,
)
from commerce_platform.web.schemas import DealsScoringConfigBody

router = APIRouter()


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
    return [deal_to_card_response(deal) for deal in deals]


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
    return [deal_to_card_response(deal) for deal in deals]


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
    # Client-side pagination: pending list is typically small (<50)
    return [deal_to_card_response(deal) for deal in deals[offset : offset + limit]]


@router.post("/deals/{deal_id}/approve")
async def admin_approve_deal(
    deal_id: int,
    note: str | None = None,
    admin=Depends(require_admin),
    deal_repo: DealRepo = Depends(get_deal_repo),
):
    """Admin approves a deal for notification to users."""
    deal = await deal_repo.get_by_id(deal_id)
    if not deal:
        raise HTTPException(404, f"Deal {deal_id} not found")
    await deal_repo.mark_reviewed(deal_id, "approved", user_id=admin.id, reason=note)
    return {"ok": True, "deal_id": deal_id, "status": "approved"}


@router.post("/deals/{deal_id}/reject")
async def admin_reject_deal(
    deal_id: int,
    reason: str | None = None,
    admin=Depends(require_admin),
    deal_repo: DealRepo = Depends(get_deal_repo),
):
    """Admin rejects a deal with optional reason."""
    deal = await deal_repo.get_by_id(deal_id)
    if not deal:
        raise HTTPException(404, f"Deal {deal_id} not found")
    await deal_repo.mark_reviewed(deal_id, "rejected", user_id=admin.id, reason=reason)
    return {"ok": True, "deal_id": deal_id, "status": "rejected", "reason": reason}
