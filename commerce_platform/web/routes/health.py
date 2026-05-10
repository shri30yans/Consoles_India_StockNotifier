"""System health checks and monitoring.

All routes live under ``/system`` (in addition to ``/health``) so they never
shadow public domain routes such as ``/deals``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from commerce_platform.platform.store.repos import DealRepo, StockRepo
from commerce_platform.web.deps import get_deal_repo, get_stock_repo

router = APIRouter(tags=["health"])
tz = timezone.utc


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Basic health check."""
    return {"status": "ok", "timestamp": datetime.now(tz).isoformat()}


@router.get("/system")
async def system_health(
    deal_repo: DealRepo = Depends(get_deal_repo),
    stock_repo: StockRepo = Depends(get_stock_repo),
) -> dict[str, Any]:
    """Full system health check with deals and stock status."""
    checks: dict[str, Any] = {
        "database": {"status": "unknown"},
        "deals": {"status": "unknown"},
        "stock": {"status": "unknown"},
        "api": {"status": "healthy"},
    }

    try:
        await deal_repo.list_active(limit=1)
        checks["database"]["status"] = "healthy"
        checks["database"]["message"] = "PostgreSQL connection OK"
    except Exception as e:
        checks["database"]["status"] = "error"
        checks["database"]["error"] = str(e)

    try:
        all_deals = await deal_repo.list_active(limit=10000)
        active_count = len(all_deals)
        pending = await deal_repo.get_pending_approval(minutes=5)
        expired = await deal_repo.list_expired(limit=100)

        by_retailer: dict[str, int] = {}
        for deal in all_deals:
            by_retailer[deal.retailer] = by_retailer.get(deal.retailer, 0) + 1

        checks["deals"]["status"] = "healthy"
        checks["deals"]["active_deals"] = active_count
        checks["deals"]["pending_approval"] = len(pending)
        checks["deals"]["expired_deals"] = len(expired)
        checks["deals"]["by_retailer"] = by_retailer
        checks["deals"]["last_updated"] = (
            max([d.last_confirmed_at for d in all_deals], default=None) if all_deals else None
        )
    except Exception as e:
        checks["deals"]["status"] = "error"
        checks["deals"]["error"] = str(e)

    overall = "healthy"
    if any(c.get("status") == "error" for c in checks.values()):
        overall = "degraded"

    return {
        "overall_status": overall,
        "checks": checks,
        "timestamp": datetime.now(tz).isoformat(),
    }


@router.get("/system/deals")
async def deals_status(deal_repo: DealRepo = Depends(get_deal_repo)) -> dict[str, Any]:
    """Detailed deals system status (diagnostic — not the public ``/deals`` API)."""
    try:
        active = await deal_repo.list_active(limit=10000)
        pending = await deal_repo.get_pending_approval(minutes=60)

        stats: dict[str, dict[str, Any]] = {}
        for deal in active:
            if deal.retailer not in stats:
                stats[deal.retailer] = {"count": 0, "avg_score": 0.0, "avg_discount": 0.0}
            stats[deal.retailer]["count"] += 1
            stats[deal.retailer]["avg_score"] += deal.score
            if deal.discount_pct:
                stats[deal.retailer]["avg_discount"] += deal.discount_pct

        for retailer in stats:
            if stats[retailer]["count"] > 0:
                stats[retailer]["avg_score"] /= stats[retailer]["count"]
                stats[retailer]["avg_discount"] /= stats[retailer]["count"]

        return {
            "status": "healthy",
            "active_deals": len(active),
            "pending_approval": len(pending),
            "by_retailer": stats,
            "timestamp": datetime.now(tz).isoformat(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "timestamp": datetime.now(tz).isoformat()}


@router.get("/system/deals/recent")
async def recent_deals(
    deal_repo: DealRepo = Depends(get_deal_repo),
    limit: int = 20,
) -> dict[str, Any]:
    """Get recently discovered deals (debug endpoint)."""
    try:
        deals = await deal_repo.list_active(limit=limit)
        return {
            "count": len(deals),
            "deals": [
                {
                    "id": d.id,
                    "retailer": d.retailer,
                    "title": d.product_title,
                    "price_inr": round(d.price_paise / 100, 2),
                    "discount_pct": round(d.discount_pct * 100, 1) if d.discount_pct else None,
                    "score": d.score,
                    "score_reasons": d.score_reasons,
                    "source": d.source,
                    "last_confirmed": d.last_confirmed_at,
                }
                for d in deals
            ],
            "timestamp": datetime.now(tz).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now(tz).isoformat()}


@router.get("/system/deals/pending-approval")
async def pending_approval(
    deal_repo: DealRepo = Depends(get_deal_repo),
    minutes: int = 60,
) -> dict[str, Any]:
    """Get deals pending admin approval (debug endpoint)."""
    try:
        deals = await deal_repo.get_pending_approval(minutes=minutes)
        return {
            "count": len(deals),
            "deals": [
                {
                    "id": d.id,
                    "retailer": d.retailer,
                    "title": d.product_title,
                    "price_inr": round(d.price_paise / 100, 2),
                    "score": d.score,
                    "score_reasons": d.score_reasons,
                    "created_at": d.first_seen_at,
                }
                for d in deals
            ],
            "timestamp": datetime.now(tz).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now(tz).isoformat()}
