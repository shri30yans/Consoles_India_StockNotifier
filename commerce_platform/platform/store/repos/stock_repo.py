"""Stock state repository — current in/out stock status per product/retailer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple

import asyncpg


class StockState(NamedTuple):
    """Current stock state for a product at a retailer."""

    product_id: str
    retailer: str
    in_stock: bool
    last_changed_at: str
    last_checked_at: str


class StockRepo:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, product_id: str, retailer: str) -> StockState | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT product_id, retailer, in_stock, last_changed_at, last_checked_at
                FROM stock_state
                WHERE product_id = $1 AND retailer = $2
                """,
                product_id,
                retailer,
            )
        if row is None:
            return None
        return StockState(
            product_id=row["product_id"],
            retailer=row["retailer"],
            in_stock=bool(row["in_stock"]),
            last_changed_at=row["last_changed_at"],
            last_checked_at=row["last_checked_at"],
        )

    async def get_batch(self, pairs: list[tuple[str, str]]) -> dict[tuple[str, str], StockState]:
        """Stock rows for (product_id, retailer) pairs in one query."""
        if not pairs:
            return {}
        pids = [a for a, _ in pairs]
        rets = [b for _, b in pairs]
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT s.product_id, s.retailer, s.in_stock, s.last_changed_at, s.last_checked_at
                FROM stock_state s
                INNER JOIN unnest($1::text[], $2::text[]) AS t(product_id, retailer)
                    ON s.product_id = t.product_id AND s.retailer = t.retailer
                """,
                pids,
                rets,
            )
        return {
            (r["product_id"], r["retailer"]): StockState(
                product_id=r["product_id"],
                retailer=r["retailer"],
                in_stock=bool(r["in_stock"]),
                last_changed_at=r["last_changed_at"],
                last_checked_at=r["last_checked_at"],
            )
            for r in rows
        }

    async def upsert(self, product_id: str, retailer: str, in_stock: bool) -> tuple[bool, bool]:
        """Upsert stock state. Returns (previous_in_stock, changed)."""
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                prev_row = await conn.fetchrow(
                    "SELECT in_stock, last_changed_at FROM stock_state WHERE product_id = $1 AND retailer = $2",
                    product_id,
                    retailer,
                )
                prev_in_stock = bool(prev_row["in_stock"]) if prev_row else False
                changed = prev_in_stock != in_stock

                await conn.execute(
                    """
                    INSERT INTO stock_state (product_id, retailer, in_stock, last_changed_at, last_checked_at)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (product_id, retailer) DO UPDATE SET
                        in_stock = $3,
                        last_changed_at = CASE WHEN stock_state.in_stock != $3 THEN $4 ELSE stock_state.last_changed_at END,
                        last_checked_at = $5
                    """,
                    product_id,
                    retailer,
                    1 if in_stock else 0,
                    now if changed else (prev_row["last_changed_at"] if prev_row else now),
                    now,
                )
        return (prev_in_stock, changed)
