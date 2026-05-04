"""Catalog repository — products, watches, and alerts (DB-backed overlay over YAML config)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, NamedTuple

import asyncpg

from commerce_platform.platform.config.schema import (
    AlertConfig,
    DefaultsConfig,
    ProductConfig,
    WatchConfig,
)
from commerce_platform.platform.text_normalization import normalize_product_name

logger = logging.getLogger(__name__)


class WatchRow(NamedTuple):
    """A catalog watch row."""

    id: int
    product_id: str
    source: str
    url: str
    asin: str | None
    affiliate_tag: str | None
    poll_seconds: int | None
    created_at: str


class CatalogRepo:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def list_overlay_as_products(self, defaults: DefaultsConfig) -> list[ProductConfig]:
        """Merge DB products with their watches and alerts into ProductConfig list."""
        products: dict[str, ProductConfig] = {}
        async with self._pool.acquire() as conn:
            product_rows = await conn.fetch(
                """
                SELECT id, name, brand, category, emoji, colour, source_request_id, created_at, image_url
                FROM catalog_products
                ORDER BY created_at
                """
            )
            for row in product_rows:
                products[row["id"]] = ProductConfig(
                    id=row["id"],
                    name=row["name"],
                    brand=row["brand"],
                    category=row["category"],
                    emoji=row["emoji"],
                    colour=row["colour"],
                    image_url=row["image_url"],
                    watches=[],
                    alerts=defaults.alerts,
                )

            watch_rows = await conn.fetch(
                """
                SELECT id, product_id, source, url, asin, affiliate_tag, poll_seconds, created_at
                FROM catalog_watches
                ORDER BY id
                """
            )
            for row in watch_rows:
                pid = row["product_id"]
                if pid not in products:
                    continue
                w = WatchConfig(
                    source=row["source"],
                    url=row["url"],
                    asin=row["asin"],
                    affiliate_tag=row["affiliate_tag"],
                    poll_seconds=row["poll_seconds"],
                )
                p = products[pid]
                products[pid] = p.model_copy(update={"watches": [*p.watches, w]})

            alert_rows = await conn.fetch(
                """
                SELECT id, product_id, alert_type, threshold_inr, threshold, channels, retailers, position
                FROM catalog_product_alerts
                ORDER BY product_id, position
                """
            )
            alerts_by_pid: dict[str, list[AlertConfig]] = {}
            for row in alert_rows:
                pid = row["product_id"]
                try:
                    channels = json.loads(row["channels"])
                    ret_raw = row["retailers"]
                    retailers = json.loads(ret_raw) if ret_raw else None
                    alert = AlertConfig(
                        type=row["alert_type"],
                        threshold_inr=row["threshold_inr"],
                        threshold=row["threshold"],
                        channels=channels,
                        retailers=retailers,
                    )
                    alerts_by_pid.setdefault(pid, []).append(alert)
                except Exception:
                    logger.warning(
                        "Skipping invalid catalog_product_alerts row id=%s product_id=%s",
                        row["id"],
                        pid,
                        exc_info=True,
                    )

            for pid, alert_list in alerts_by_pid.items():
                if pid not in products:
                    continue
                p = products[pid]
                products[pid] = p.model_copy(update={"alerts": alert_list})

        return [p for p in products.values() if p.watches]

    async def list_product_ids(self) -> set[str]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT id FROM catalog_products")
        return {str(r["id"]) for r in rows}

    async def normalize_stored_product_names(self) -> list[tuple[str, str, str]]:
        """Apply normalize_product_name to every catalog_products row and persist changes.

        Returns ``[(product_id, old_name, new_name), ...]`` for rows that were updated.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, name FROM catalog_products ORDER BY id")
        updates: list[tuple[str, str, str]] = []
        for row in rows:
            old = row["name"]
            new = normalize_product_name(old)
            if new != old:
                updates.append((str(row["id"]), old, new))
        if not updates:
            return []
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for pid, _old, new in updates:
                    await conn.execute(
                        "UPDATE catalog_products SET name = $1 WHERE id = $2",
                        new,
                        pid,
                    )
        return updates

    async def list_watches_for_product(self, product_id: str) -> list[WatchRow]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, product_id, source, url, asin, affiliate_tag, poll_seconds, created_at
                FROM catalog_watches
                WHERE product_id = $1
                ORDER BY id
                """,
                product_id,
            )
        return [
            WatchRow(
                id=r["id"],
                product_id=r["product_id"],
                source=r["source"],
                url=r["url"],
                asin=r["asin"],
                affiliate_tag=r["affiliate_tag"],
                poll_seconds=r["poll_seconds"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    async def get_product_id_by_retailer_sku(self, retailer: str, sku: str) -> str | None:
        """Resolve product_id from retailer+SKU (ASIN, product code, etc.)."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchval(
                """
                SELECT product_id
                FROM catalog_product_identifiers
                WHERE retailer = $1 AND sku = $2
                LIMIT 1
                """,
                retailer,
                sku,
            )
        return row

    async def list_identifiers_for_product(self, product_id: str) -> dict[str, str]:
        """Get all retailer SKUs for a product. Returns {retailer: sku}."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT retailer, sku
                FROM catalog_product_identifiers
                WHERE product_id = $1
                """,
                product_id,
            )
        return {row["retailer"]: row["sku"] for row in rows}

    async def upsert_identifier(self, product_id: str, retailer: str, sku: str) -> None:
        """Add or update product identifier (retailer SKU)."""
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO catalog_product_identifiers (product_id, retailer, sku, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (product_id, retailer) DO UPDATE SET
                    sku = $3
                """,
                product_id,
                retailer,
                sku,
                now,
            )

    async def list_all_rules(self) -> list[dict]:
        """Load all enabled rules from database."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT rule_id, product_id, rule_type, threshold_inr, threshold_pct, channels, retailers
                FROM catalog_rules
                WHERE enabled = true
                ORDER BY product_id, position
                """
            )
        rules = []
        for row in rows:
            try:
                channels = json.loads(row["channels"]) if isinstance(row["channels"], str) else row["channels"] or []
                retailers = json.loads(row["retailers"]) if row["retailers"] else None
                rules.append(
                    {
                        "rule_id": row["rule_id"],
                        "product_id": row["product_id"],
                        "rule_type": row["rule_type"],
                        "threshold_inr": row["threshold_inr"],
                        "threshold_pct": row["threshold_pct"],
                        "channels": channels,
                        "retailers": retailers,
                    }
                )
            except Exception:
                logger.warning("Skipping invalid rule row: %s", row["rule_id"], exc_info=True)
        return rules

    async def upsert_rule(
        self,
        product_id: str,
        rule_id: str,
        rule_type: str,
        threshold_inr: float | None,
        threshold_pct: float | None,
        channels: list[str],
        retailers: list[str] | None = None,
    ) -> None:
        """Add or update a rule."""
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO catalog_rules
                (product_id, rule_id, rule_type, threshold_inr, threshold_pct, channels, retailers, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (product_id, rule_id) DO UPDATE SET
                    rule_type = $3,
                    threshold_inr = $4,
                    threshold_pct = $5,
                    channels = $6,
                    retailers = $7
                """,
                product_id,
                rule_id,
                rule_type,
                threshold_inr,
                threshold_pct,
                json.dumps(channels),
                json.dumps(retailers) if retailers else None,
                now,
            )

    async def delete_rule(self, product_id: str, rule_id: str) -> bool:
        """Delete a rule."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM catalog_rules WHERE product_id = $1 AND rule_id = $2",
                product_id,
                rule_id,
            )
        return "0" not in str(result)

    async def upsert_product(
        self,
        product_id: str,
        name: str,
        brand: str | None,
        category: str,
        emoji: str | None,
        colour: int | None,
        image_url: str | None,
    ) -> None:
        name = normalize_product_name(name)
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO catalog_products(id, name, brand, category, emoji, colour, source_request_id, created_at, image_url)
                VALUES ($1, $2, $3, $4, $5, $6, NULL, $7, $8)
                ON CONFLICT (id) DO UPDATE SET
                    name = $2,
                    brand = $3,
                    category = $4,
                    emoji = $5,
                    colour = $6,
                    image_url = COALESCE($8, catalog_products.image_url)
                """,
                product_id,
                name,
                brand,
                category,
                emoji,
                colour,
                now,
                image_url,
            )

    async def insert_watch(
        self,
        product_id: str,
        source: str,
        url: str,
        asin: str | None,
        affiliate_tag: str | None,
        poll_seconds: int | None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO catalog_watches(product_id, source, url, asin, affiliate_tag, poll_seconds, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                product_id,
                source,
                url,
                asin,
                affiliate_tag,
                poll_seconds,
                now,
            )
        return int(row["id"])

    async def update_watch(
        self,
        watch_id: int,
        source: str,
        url: str,
        asin: str | None,
        affiliate_tag: str | None,
        poll_seconds: int | None,
    ) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE catalog_watches
                SET source = $1, url = $2, asin = $3, affiliate_tag = $4, poll_seconds = $5
                WHERE id = $6
                """,
                source,
                url,
                asin,
                affiliate_tag,
                poll_seconds,
                watch_id,
            )
        return "0" not in str(result)

    async def delete_watch(self, watch_id: int) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM catalog_watches WHERE id = $1",
                watch_id,
            )
        return "0" not in str(result)

    async def get_watch(self, watch_id: int) -> WatchRow | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, product_id, source, url, asin, affiliate_tag, poll_seconds, created_at FROM catalog_watches WHERE id = $1",
                watch_id,
            )
        if row is None:
            return None
        return WatchRow(
            id=row["id"],
            product_id=row["product_id"],
            source=row["source"],
            url=row["url"],
            asin=row["asin"],
            affiliate_tag=row["affiliate_tag"],
            poll_seconds=row["poll_seconds"],
            created_at=row["created_at"],
        )

    async def ensure_product_and_add_watch(
        self,
        product_id: str,
        name: str,
        brand: str | None,
        category: str,
        source: str,
        url: str,
        asin: str | None,
        affiliate_tag: str | None,
        poll_seconds: int | None,
        source_request_id: int | None,
        image_url: str | None = None,
    ) -> None:
        name = normalize_product_name(name)
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                exists = await conn.fetchval(
                    "SELECT 1 FROM catalog_products WHERE id = $1",
                    product_id,
                )
                if not exists:
                    await conn.execute(
                        """
                        INSERT INTO catalog_products(id, name, brand, category, emoji, colour,
                                                    source_request_id, created_at, image_url)
                        VALUES ($1, $2, $3, $4, NULL, NULL, $5, $6, $7)
                        """,
                        product_id,
                        name,
                        brand or None,
                        category,
                        source_request_id,
                        now,
                        image_url,
                    )
                elif image_url:
                    await conn.execute(
                        "UPDATE catalog_products SET image_url = $1 WHERE id = $2",
                        image_url,
                        product_id,
                    )

                await conn.execute(
                    """
                    INSERT INTO catalog_watches(product_id, source, url, asin, affiliate_tag,
                                                poll_seconds, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    product_id,
                    source,
                    url,
                    asin,
                    affiliate_tag,
                    poll_seconds,
                    now,
                )

    async def bulk_upsert_from_config(
        self, products: list[ProductConfig], *, replace_children: bool = True
    ) -> None:
        """Bulk upsert products from config, optionally replacing their watches/alerts."""
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for product in products:
                    normalized_name = normalize_product_name(product.name)
                    await conn.execute(
                        """
                        INSERT INTO catalog_products(id, name, brand, category, emoji, colour,
                                                    source_request_id, created_at, image_url)
                        VALUES ($1, $2, $3, $4, $5, $6, NULL, $7, $8)
                        ON CONFLICT (id) DO UPDATE SET
                            name = $2,
                            brand = $3,
                            category = $4,
                            emoji = $5,
                            colour = $6,
                            image_url = COALESCE($8, catalog_products.image_url)
                        """,
                        product.id,
                        normalized_name,
                        product.brand,
                        product.category,
                        product.emoji,
                        product.colour,
                        now,
                        product.image_url,
                    )

                    if replace_children:
                        await conn.execute("DELETE FROM catalog_watches WHERE product_id = $1", product.id)
                        await conn.execute("DELETE FROM catalog_product_alerts WHERE product_id = $1", product.id)

                    for watch in product.watches:
                        await conn.execute(
                            """
                            INSERT INTO catalog_watches(product_id, source, url, asin, affiliate_tag,
                                                        poll_seconds, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """,
                            product.id,
                            watch.source,
                            watch.url,
                            watch.asin,
                            watch.affiliate_tag,
                            watch.poll_seconds,
                            now,
                        )

                    for idx, alert in enumerate(product.alerts):
                        await conn.execute(
                            """
                            INSERT INTO catalog_product_alerts(product_id, alert_type, threshold_inr,
                                                              threshold, channels, retailers, position)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """,
                            product.id,
                            alert.type,
                            alert.threshold_inr,
                            alert.threshold,
                            json.dumps(alert.channels),
                            json.dumps(alert.retailers) if alert.retailers else None,
                            idx,
                        )
