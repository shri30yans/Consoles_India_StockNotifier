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
                emoji TEXT,
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

    await db.close()
    print("Database schema initialized successfully!")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    config_path = Path(os.environ.get("PLATFORM_CONFIG", "config.yaml")).resolve()
    asyncio.run(init_db(config_path))
