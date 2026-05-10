"""Initialize database schema.

This module is the source of truth for **fresh-install** PostgreSQL DDL in this repo.
It was rewritten on 2026-05-10 to align ``CREATE TABLE`` shapes with
``commerce_platform/platform/store/repos/*.py`` (insert/select/update patterns).

Recommended btree indexes for production workloads also live in
``scripts/sql/recommended_indexes.sql``; that file uses ``CREATE INDEX CONCURRENTLY``,
which cannot run inside a transaction (see PostgreSQL docs). This script embeds the
same logical indexes without ``CONCURRENTLY`` so a single ``init_db`` run stays simple.

Timestamps are stored as ``TEXT`` holding ISO-8601 strings where application code uses
``datetime.now(timezone.utc).isoformat()``, matching existing rows and casts like
``created_at::TIMESTAMP`` in ``DealRepo``.
"""

import asyncio
from pathlib import Path

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database


async def init_db(config_path: Path) -> None:
    """Create all required tables."""
    config = load(config_path)
    db = Database(config.platform.store)
    await db.open()

    async with db.pool.acquire() as conn:
        # catalog_products — CatalogRepo
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS catalog_products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                brand TEXT,
                category TEXT NOT NULL,
                colour INTEGER,
                source_request_id INTEGER,
                created_at TEXT NOT NULL,
                image_url TEXT
            )
        """)

        # app_users — UserRepo (before tracking_requests FK)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            )
        """)

        # catalog_watches — CatalogRepo
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS catalog_watches (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                asin TEXT,
                affiliate_tag TEXT,
                poll_seconds INTEGER,
                created_at TEXT NOT NULL
            )
        """)

        # catalog_product_alerts — CatalogRepo (insert omits created_at → default)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS catalog_product_alerts (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                alert_type TEXT NOT NULL,
                threshold_inr FLOAT,
                threshold FLOAT,
                channels TEXT NOT NULL,
                retailers TEXT,
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # catalog_product_identifiers — CatalogRepo upsert ON CONFLICT (product_id, retailer)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS catalog_product_identifiers (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                retailer TEXT NOT NULL,
                sku TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(product_id, retailer)
            )
        """)

        # catalog_rules — CatalogRepo (insert omits enabled/position → defaults)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS catalog_rules (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                rule_id TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                threshold_inr FLOAT,
                threshold_pct FLOAT,
                channels TEXT NOT NULL,
                retailers TEXT,
                enabled BOOLEAN NOT NULL DEFAULT true,
                position INTEGER,
                created_at TEXT NOT NULL,
                UNIQUE(product_id, rule_id)
            )
        """)

        # tracking_requests — TrackingRepo (integer user_id → app_users)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tracking_requests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES app_users(id),
                raw_url TEXT NOT NULL,
                normalized_retailer_hint TEXT,
                desired_product_name TEXT,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                admin_note TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                decided_by INTEGER REFERENCES app_users(id),
                promoted_product_id TEXT REFERENCES catalog_products(id)
            )
        """)

        # price_snapshots — PriceRepo (append-only; no created_at column)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS price_snapshots (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                retailer TEXT NOT NULL,
                price_paise INTEGER NOT NULL,
                mrp_paise INTEGER,
                in_stock BOOLEAN NOT NULL,
                captured_at TEXT NOT NULL
            )
        """)

        # stock_state — StockRepo ON CONFLICT (product_id, retailer)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_state (
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                retailer TEXT NOT NULL,
                in_stock BOOLEAN NOT NULL,
                last_changed_at TEXT NOT NULL,
                last_checked_at TEXT NOT NULL,
                PRIMARY KEY (product_id, retailer)
            )
        """)

        # config_settings — ConfigSettingsRepo
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS config_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # deals — DealRepo (insert omits created_at → default)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id SERIAL PRIMARY KEY,
                product_url TEXT NOT NULL UNIQUE,
                product_id TEXT REFERENCES catalog_products(id),
                retailer TEXT NOT NULL,
                price_paise INTEGER NOT NULL,
                mrp_paise INTEGER,
                discount_pct FLOAT,
                score FLOAT NOT NULL DEFAULT 0.0,
                score_reasons TEXT NOT NULL DEFAULT '[]',
                product_title TEXT,
                image_url TEXT,
                source TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT true,
                last_notified_at TEXT,
                first_seen_at TEXT NOT NULL,
                last_confirmed_at TEXT NOT NULL,
                admin_status TEXT,
                admin_reviewed_by INTEGER,
                admin_reviewed_at TEXT,
                admin_review_note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- Indexes (see scripts/sql/recommended_indexes.sql; no CONCURRENTLY here) ---
        # catalog_product_identifiers: resolver WHERE retailer = $1 AND sku = $2
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_catalog_product_identifiers_retailer_sku
            ON catalog_product_identifiers (retailer, sku)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_snapshots_product_retailer_captured
            ON price_snapshots (product_id, retailer, captured_at DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_catalog_product_alerts_product_position
            ON catalog_product_alerts (product_id, position)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_catalog_watches_product_id
            ON catalog_watches (product_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_catalog_rules_enabled_product
            ON catalog_rules (product_id)
            WHERE enabled = true
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tracking_requests_user_created
            ON tracking_requests (user_id, created_at DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tracking_requests_status_created
            ON tracking_requests (status, created_at DESC)
        """)

        # idx_app_users_email: omitted — UNIQUE(email) on app_users already provides btree lookup.

        # deals — DealRepo list/filter queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS deals_active_score ON deals(is_active, score DESC)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS deals_product_id ON deals(product_id, is_active)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS deals_retailer ON deals(retailer, is_active)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS deals_admin_status ON deals(admin_status, created_at DESC)
        """)

    await db.close()
    print("Database schema initialized successfully!")


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    config_path = Path(os.environ.get("PLATFORM_CONFIG", "config.yaml")).resolve()
    asyncio.run(init_db(config_path))
