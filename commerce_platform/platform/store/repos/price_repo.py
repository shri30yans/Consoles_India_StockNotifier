"""Price history repository — append-only snapshots and aggregates."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, NamedTuple

import asyncpg


class PriceSnapshot(NamedTuple):
    """A price snapshot row from price_snapshots table."""

    id: int | None
    product_id: str
    retailer: str
    price_paise: int
    mrp_paise: int | None
    in_stock: bool
    captured_at: str


class PriceRow(NamedTuple):
    """Price list row (for chart data)."""

    price_paise: int
    in_stock: bool
    captured_at: str


class PriceRepo:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_latest_snapshot(self, product_id: str, retailer: str) -> PriceSnapshot | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, product_id, retailer, price_paise, mrp_paise, in_stock, captured_at
                FROM price_snapshots
                WHERE product_id = $1 AND retailer = $2
                ORDER BY captured_at DESC
                LIMIT 1
                """,
                product_id,
                retailer,
            )
        if row is None:
            return None
        return PriceSnapshot(
            id=row["id"],
            product_id=row["product_id"],
            retailer=row["retailer"],
            price_paise=row["price_paise"],
            mrp_paise=row["mrp_paise"],
            in_stock=bool(row["in_stock"]),
            captured_at=row["captured_at"],
        )

    async def get_latest_snapshots_batch(
        self, pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], PriceSnapshot]:
        """Latest snapshot per (product_id, retailer) in at most one round-trip."""
        if not pairs:
            return {}
        pids = [a for a, _ in pairs]
        rets = [b for _, b in pairs]
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (ps.product_id, ps.retailer)
                    ps.id,
                    ps.product_id,
                    ps.retailer,
                    ps.price_paise,
                    ps.mrp_paise,
                    ps.in_stock,
                    ps.captured_at
                FROM price_snapshots ps
                INNER JOIN unnest($1::text[], $2::text[]) AS t(product_id, retailer)
                    ON ps.product_id = t.product_id AND ps.retailer = t.retailer
                ORDER BY ps.product_id, ps.retailer, ps.captured_at DESC
                """,
                pids,
                rets,
            )
        out: dict[tuple[str, str], PriceSnapshot] = {}
        for row in rows:
            key = (row["product_id"], row["retailer"])
            out[key] = PriceSnapshot(
                id=row["id"],
                product_id=row["product_id"],
                retailer=row["retailer"],
                price_paise=row["price_paise"],
                mrp_paise=row["mrp_paise"],
                in_stock=bool(row["in_stock"]),
                captured_at=row["captured_at"],
            )
        return out

    async def record(self, snap: PriceSnapshot) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO price_snapshots(product_id, retailer, price_paise, mrp_paise, in_stock, captured_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                snap.product_id,
                snap.retailer,
                snap.price_paise,
                snap.mrp_paise,
                1 if snap.in_stock else 0,
                snap.captured_at,
            )

    async def min_price(self, product_id: str, retailer: str | None, *, days: int) -> int | None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        async with self._pool.acquire() as conn:
            if retailer is None:
                row = await conn.fetchrow(
                    """
                    SELECT MIN(price_paise) as min_price
                    FROM price_snapshots
                    WHERE product_id = $1 AND captured_at >= $2
                    """,
                    product_id,
                    cutoff,
                )
            else:
                row = await conn.fetchrow(
                    """
                    SELECT MIN(price_paise) as min_price
                    FROM price_snapshots
                    WHERE product_id = $1 AND retailer = $2 AND captured_at >= $3
                    """,
                    product_id,
                    retailer,
                    cutoff,
                )
        return row["min_price"] if row and row["min_price"] is not None else None

    async def median_price(self, product_id: str, retailer: str | None, *, days: int) -> int | None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        async with self._pool.acquire() as conn:
            if retailer is None:
                rows = await conn.fetch(
                    """
                    SELECT price_paise
                    FROM price_snapshots
                    WHERE product_id = $1 AND captured_at >= $2
                    ORDER BY price_paise
                    """,
                    product_id,
                    cutoff,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT price_paise
                    FROM price_snapshots
                    WHERE product_id = $1 AND retailer = $2 AND captured_at >= $3
                    ORDER BY price_paise
                    """,
                    product_id,
                    retailer,
                    cutoff,
                )
        if not rows:
            return None
        prices = [r["price_paise"] for r in rows]
        n = len(prices)
        if n % 2 == 1:
            return prices[n // 2]
        return (prices[n // 2 - 1] + prices[n // 2]) // 2

    async def cross_retailer_min(self, product_id: str) -> int | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT MIN(price_paise) as min_price
                FROM (
                    SELECT DISTINCT ON (retailer) price_paise
                    FROM price_snapshots
                    WHERE product_id = $1
                    ORDER BY retailer, captured_at DESC
                ) latest
                """,
                product_id,
            )
        return row["min_price"] if row and row["min_price"] is not None else None

    async def snapshot_count(self, product_id: str, retailer: str, *, days: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(*) as cnt
                FROM price_snapshots
                WHERE product_id = $1 AND retailer = $2 AND captured_at >= $3
                """,
                product_id,
                retailer,
                cutoff,
            )
        return row["cnt"] if row else 0

    async def list_price_series(
        self, product_id: str, retailer: str | None, *, days: int, limit: int = 800
    ) -> list[PriceRow]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        async with self._pool.acquire() as conn:
            if retailer is None:
                rows = await conn.fetch(
                    """
                    SELECT price_paise, in_stock, captured_at
                    FROM price_snapshots
                    WHERE product_id = $1 AND captured_at >= $2
                    ORDER BY captured_at ASC
                    LIMIT $3
                    """,
                    product_id,
                    cutoff,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT price_paise, in_stock, captured_at
                    FROM price_snapshots
                    WHERE product_id = $1 AND retailer = $2 AND captured_at >= $3
                    ORDER BY captured_at ASC
                    LIMIT $4
                    """,
                    product_id,
                    retailer,
                    cutoff,
                    limit,
                )
        return [
            PriceRow(price_paise=r["price_paise"], in_stock=bool(r["in_stock"]), captured_at=r["captured_at"])
            for r in rows
        ]
