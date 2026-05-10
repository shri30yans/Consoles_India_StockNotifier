#!/usr/bin/env python3
"""Fire a test PriceObservation to verify the notification pipeline end-to-end.

Bypasses scrapers entirely — injects an observation directly and shows which
rules matched and whether notifications were sent to channels.

Usage:
    python scripts/fire_test_notification.py
    python scripts/fire_test_notification.py --product-id ps5_slim_base --price 30000
    python scripts/fire_test_notification.py --retailer flipkart --price 45000

Flags:
    --product-id  Catalog product ID (default: first one found in DB)
    --price       Test price in rupees (default: 30000 — typically triggers back_in_stock)
    --retailer    Retailer name: amazon | flipkart (default: amazon)
    --in-stock    Simulate in-stock (default: True)
    --dry-run     Evaluate rules but skip sending notifications
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main(
    product_id: str | None,
    price_rupees: float,
    retailer: str,
    in_stock: bool,
    dry_run: bool,
) -> None:
    from commerce_platform.platform.config.loader import load
    from commerce_platform.platform.events.observation import PriceObservation
    from commerce_platform.platform.notify.affiliate import AffiliateRewriter
    from commerce_platform.platform.notify.handler import NotificationHandler
    from commerce_platform.platform.notify.router import ChannelRouter
    from commerce_platform.platform.store.db import Database
    from commerce_platform.platform.store.repos import (
        CatalogRepo,
        ConfigSettingsRepo,
        PriceRepo,
        StockRepo,
    )
    from commerce_platform.rules.engine import RuleEngine

    load_dotenv(Path(".env"), override=True)
    config = load(Path("config.yaml"))
    db = Database(config.platform.store)
    await db.open()

    try:
        catalog_repo = CatalogRepo(db.pool)
        config_repo = ConfigSettingsRepo(db.pool)
        price_repo = PriceRepo(db.pool)
        stock_repo = StockRepo(db.pool)

        # Resolve product_id if not provided
        if not product_id:
            ids = await catalog_repo.list_product_ids()
            if not ids:
                print("No products found in DB. Run scripts/backfill_products.py first.")
                return
            product_id = sorted(ids)[0]
            print(f"No --product-id given, using first found: {product_id}")

        rule_engine = RuleEngine(catalog_repo, price_repo, stock_repo)
        await rule_engine.reload_rules()

        obs = PriceObservation(
            product_id=product_id,
            retailer=retailer,
            price_paise=int(price_rupees * 100),
            mrp_paise=None,
            in_stock=in_stock,
            source="test:fire_test_notification",
            observed_at=datetime.now(timezone.utc).isoformat(),
            product_url=f"https://www.{'amazon.in/dp/TEST' if retailer == 'amazon' else 'flipkart.com/test/p/TEST'}",
            product_title=f"[TEST] {product_id}",
        )

        print()
        print(f"Observation: product={product_id}  retailer={retailer}  price=₹{price_rupees:,.0f}  in_stock={in_stock}")
        print()

        matches = await rule_engine.evaluate(obs)

        if not matches:
            print("No rules matched.")
            print("  → Check that rules are configured in the DB for this product.")
            print("  → Or try a lower --price to trigger a price_below rule.")
            return

        print(f"Rules matched: {len(matches)}")
        for match in matches:
            print(f"  {match.rule_id}  type={match.rule_type}  channels={match.channels}")
        print()

        if dry_run:
            print("[dry-run] Skipping send.")
            return

        router = ChannelRouter(config.channels)
        affiliate_rewriter = AffiliateRewriter(config_repo)
        handler = NotificationHandler(router, affiliate_rewriter=affiliate_rewriter)

        for match in matches:
            await handler.handle_rule_match(match)

        print("Done — check Telegram/Discord for the test notification.")

    finally:
        await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fire a test notification through the pipeline")
    parser.add_argument("--product-id", default=None, help="Catalog product ID")
    parser.add_argument("--price", type=float, default=30000, help="Price in rupees (default: 30000)")
    parser.add_argument("--retailer", default="amazon", choices=["amazon", "flipkart"], help="Retailer")
    parser.add_argument("--out-of-stock", action="store_true", help="Simulate out-of-stock (default: in-stock)")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate rules but do not send notifications")
    args = parser.parse_args()

    asyncio.run(main(
        product_id=args.product_id,
        price_rupees=args.price,
        retailer=args.retailer,
        in_stock=not args.out_of_stock,
        dry_run=args.dry_run,
    ))
