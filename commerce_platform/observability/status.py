"""Merge platform.yaml intent with DB evidence for a single status snapshot."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from commerce_platform.platform.config.merge import load_merged_platform_config
from commerce_platform.platform.config.schema import Money, PlatformSourceConfig
from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import CatalogRepo, PriceRepo, StockRepo


def _health_age_seconds(
    last: str | None, now: datetime, poll_seconds: int
) -> tuple[str, float | None]:
    if last is None:
        return "unknown", None
    try:
        last_dt = datetime.fromisoformat(last)
    except (ValueError, TypeError):
        return "unknown", None
    age = max(0.0, (now - last_dt).total_seconds())
    if poll_seconds <= 0:
        return "unknown", age
    if age <= poll_seconds * 2:
        return "ok", age
    if age <= poll_seconds * 5:
        return "warn", age
    return "stale", age


def _source_key_for_platform_source(src: PlatformSourceConfig) -> str | None:
    if src.type == "desidime":
        return "aggregator:desidime"
    if src.type == "reddit":
        return "aggregator:reddit"
    if src.type == "amazon_wishlist":
        return "platform:amazon_wishlist"
    return None


async def build_status_payload(yaml_path: str | Path, db: Database) -> dict:
    catalog_repo = CatalogRepo(db.pool)
    price_repo = PriceRepo(db.pool)
    stock_repo = StockRepo(db.pool)
    config = await load_merged_platform_config(yaml_path, catalog_repo)
    now = datetime.now(timezone.utc)
    deal_stats: dict = {}

    watches: list[dict] = []
    for product in config.products:
        for watch in product.watches:
            poll_s = config.resolve_poll_seconds(watch)
            snap = await price_repo.get_latest_snapshot(product.id, watch.source)
            st = await stock_repo.get(product.id, watch.source)
            last: str | None = None
            if snap and st:
                last = max(snap.captured_at, st.last_checked_at)
            elif snap:
                last = snap.captured_at
            elif st:
                last = st.last_checked_at
            health, age_s = _health_age_seconds(last, now, poll_s)
            watches.append(
                {
                    "kind": "product_watch",
                    "product_id": product.id,
                    "product_name": product.name,
                    "retailer": watch.source,
                    "poll_seconds": poll_s,
                    "url": watch.url,
                    "last_scrape_at": last,
                    "age_seconds": round(age_s, 1) if age_s is not None else None,
                    "health": health,
                    "in_stock": snap.in_stock if snap else (st.in_stock if st else None),
                    "price_inr": Money(snap.price_paise).to_rupees() if snap else None,
                }
            )

    platform_sources: list[dict] = []
    for src in config.platform_sources:
        key = _source_key_for_platform_source(src)
        extra = deal_stats.get(key, {}) if key else {}
        last_deal = extra.get("last_deal_at")
        health, age_s = _health_age_seconds(
            last_deal,
            now,
            src.poll_seconds,
        )
        if last_deal is None:
            health = "unknown"
            age_s = None
        base = src.model_dump()
        platform_sources.append(
            {
                **base,
                "kind": "platform_source",
                "deal_source_key": key,
                "last_deal_activity_at": last_deal,
                "deal_stats": extra if extra else None,
                "health": health,
                "age_seconds": round(age_s, 1) if age_s is not None else None,
            }
        )

    ok_n = sum(1 for w in watches if w["health"] == "ok")
    summary = {
        "generated_at": now.isoformat(),
        "product_watches_total": len(watches),
        "product_watches_ok": ok_n,
        "product_watches_warn": sum(1 for w in watches if w["health"] == "warn"),
        "product_watches_stale": sum(1 for w in watches if w["health"] == "stale"),
        "product_watches_unknown": sum(1 for w in watches if w["health"] == "unknown"),
        "platform_sources_total": len(platform_sources),
    }

    return {
        "summary": summary,
        "watches": watches,
        "platform_sources": platform_sources,
        "deal_sources_in_db": deal_stats,
    }
