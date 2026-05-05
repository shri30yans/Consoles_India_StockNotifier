"""Initialize database schema."""

import asyncio
import asyncpg
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from pathlib import Path


async def init_db(config_path: Path) -> None:
    """Create all required tables."""
    config = load(config_path)
    db = Database(config.platform.store)
    await db.open()

    async with db.pool.acquire() as conn:
        # catalog_products table
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

        # catalog_watches table
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

        # catalog_product_alerts table
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

        # catalog_product_identifiers table
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

        # catalog_rules table
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
                enabled BOOLEAN DEFAULT true,
                position INTEGER,
                created_at TEXT NOT NULL,
                UNIQUE(product_id, rule_id)
            )
        """)

        # price_snapshots table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS price_snapshots (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                retailer TEXT NOT NULL,
                price_inr FLOAT,
                currency TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # stock_state table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_state (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                retailer TEXT NOT NULL,
                in_stock BOOLEAN NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, retailer)
            )
        """)

        # app_users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            )
        """)

        # tracking_requests table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tracking_requests (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES catalog_products(id),
                user_id TEXT NOT NULL,
                request_type TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # config_settings table — admin-editable config stored in DB (JSON values)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS config_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # deals table — confirmed good deals (upsert semantics, not append-only)
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

        # Add approval tracking columns to existing deals table (if not already present)
        try:
            await conn.execute("""
                ALTER TABLE deals
                ADD COLUMN IF NOT EXISTS admin_status TEXT,
                ADD COLUMN IF NOT EXISTS admin_reviewed_by INTEGER,
                ADD COLUMN IF NOT EXISTS admin_reviewed_at TEXT,
                ADD COLUMN IF NOT EXISTS admin_review_note TEXT
            """)
        except Exception:
            pass  # Columns may already exist; ignore errors

        # Indexes for deals table
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
