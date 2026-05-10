"""Deal repository — manages the deals table with upsert semantics."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

import asyncpg

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DealRow:
    """A row in the deals table."""

    id: int | None
    product_url: str
    product_id: str | None
    retailer: str
    price_paise: int
    mrp_paise: int | None
    discount_pct: float | None
    score: float
    score_reasons: list[str]
    product_title: str | None
    image_url: str | None
    source: str
    is_active: bool
    last_notified_at: str | None
    first_seen_at: str
    last_confirmed_at: str


UpsertAction = Literal["inserted", "price_improved", "reactivated", "confirmed", "expired"]


class DealRepo:
    """Manage deals table with upsert semantics (one row per URL)."""

    def __init__(self, pool: asyncpg.pool.Pool) -> None:
        self._pool = pool

    def _row_to_dealrow(self, row: asyncpg.Record) -> DealRow:
        """Convert database row to DealRow. Single canonical method."""
        return DealRow(
            id=row["id"],
            product_url=row["product_url"],
            product_id=row["product_id"],
            retailer=row["retailer"],
            price_paise=row["price_paise"],
            mrp_paise=row["mrp_paise"],
            discount_pct=row["discount_pct"],
            score=row["score"],
            score_reasons=json.loads(row.get("score_reasons") or "[]"),
            product_title=row["product_title"],
            image_url=row["image_url"],
            source=row["source"],
            is_active=row["is_active"],
            last_notified_at=row["last_notified_at"],
            first_seen_at=row["first_seen_at"],
            last_confirmed_at=row["last_confirmed_at"],
        )

    async def get_by_url(self, url: str) -> DealRow | None:
        """Get a deal row by product URL."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM deals WHERE product_url = $1", url)
        return self._row_to_dealrow(row) if row else None

    async def upsert(self, row: DealRow) -> tuple[UpsertAction, bool]:
        """
        Upsert a deal row.

        Returns:
            (action, should_notify) where action is one of:
            - "inserted": new deal, notify if score >= threshold
            - "price_improved": price dropped by >2%, notify if score >= threshold
            - "reactivated": deal was expired, price came back down, notify if score >= threshold
            - "confirmed": same price, just updating last_confirmed_at
            - "expired": price rose or OOS, setting is_active=0

            should_notify is True only for inserted/price_improved/reactivated above threshold.
        """
        async with self._pool.acquire() as conn:
            # Check if URL already exists
            existing = await conn.fetchrow(
                "SELECT id, price_paise, is_active, score FROM deals WHERE product_url = $1",
                row.product_url,
            )

        if existing is None:
            # New deal — INSERT and notify if score is good
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO deals
                    (product_url, product_id, retailer, price_paise, mrp_paise, discount_pct,
                     score, score_reasons, product_title, image_url, source, is_active,
                     last_notified_at, first_seen_at, last_confirmed_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    """,
                    row.product_url,
                    row.product_id,
                    row.retailer,
                    row.price_paise,
                    row.mrp_paise,
                    row.discount_pct,
                    row.score,
                    json.dumps(row.score_reasons),
                    row.product_title,
                    row.image_url,
                    row.source,
                    True,
                    None,
                    row.first_seen_at,
                    row.last_confirmed_at,
                )
            return ("inserted", True)

        # URL exists — decide action based on price and is_active
        old_price = existing["price_paise"]
        was_active = existing["is_active"]
        old_score = existing["score"]

        if row.price_paise > old_price:
            # Price rose → expire
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "UPDATE deals SET is_active = false WHERE product_url = $1",
                    row.product_url,
                )
            return ("expired", False)

        if row.price_paise == old_price and was_active:
            # Same price, still active → just update confirmed time (no notify)
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "UPDATE deals SET last_confirmed_at = $1 WHERE product_url = $2",
                    row.last_confirmed_at,
                    row.product_url,
                )
            return ("confirmed", False)

        if row.price_paise < old_price and was_active:
            # Price improved → update and notify
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE deals
                    SET price_paise = $1, discount_pct = $2, score = $3,
                        score_reasons = $4, last_confirmed_at = $5
                    WHERE product_url = $6
                    """,
                    row.price_paise,
                    row.discount_pct,
                    row.score,
                    json.dumps(row.score_reasons),
                    row.last_confirmed_at,
                    row.product_url,
                )
            return ("price_improved", True)

        if not was_active and row.price_paise <= old_price:
            # Deal was expired, price came back — reactivate and notify
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE deals
                    SET is_active = true, price_paise = $1, discount_pct = $2,
                        score = $3, score_reasons = $4, last_confirmed_at = $5
                    WHERE product_url = $6
                    """,
                    row.price_paise,
                    row.discount_pct,
                    row.score,
                    json.dumps(row.score_reasons),
                    row.last_confirmed_at,
                    row.product_url,
                )
            return ("reactivated", True)

        # Fallback (shouldn't reach here)
        return ("confirmed", False)

    async def list_active(
        self,
        *,
        retailer: str | None = None,
        min_discount: float | None = None,
        min_score: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DealRow]:
        """List active deals, optionally filtered by retailer/discount/score."""
        query = "SELECT * FROM deals WHERE is_active = true"
        params: list[Any] = []

        if retailer:
            query += f" AND retailer = ${len(params) + 1}"
            params.append(retailer)
        if min_discount is not None:
            query += f" AND discount_pct >= ${len(params) + 1}"
            params.append(min_discount)
        if min_score > 0.0:
            query += f" AND score >= ${len(params) + 1}"
            params.append(min_score)

        query += " ORDER BY score DESC, last_confirmed_at DESC"
        query += f" LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_dealrow(row) for row in rows]

    async def list_expired(
        self,
        *,
        product_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DealRow]:
        """List expired deals."""
        query = "SELECT * FROM deals WHERE is_active = false"
        params: list[Any] = []

        if product_id:
            query += f" AND product_id = ${len(params) + 1}"
            params.append(product_id)

        query += " ORDER BY first_seen_at DESC"
        query += f" LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_dealrow(row) for row in rows]

    async def expire_stale(self, *, older_than_hours: int = 12) -> int:
        """Mark deals as inactive if not confirmed recently."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE deals
                SET is_active = false
                WHERE is_active = true
                AND last_confirmed_at::TIMESTAMP < NOW() - MAKE_INTERVAL(hours := $1)
                """,
                older_than_hours,
            )
        # result is a string like "UPDATE 5", extract the count
        count = int(result.split()[-1]) if result else 0
        return count

    async def get_by_id(self, deal_id: int) -> DealRow | None:
        """Get a deal by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM deals WHERE id = $1", deal_id)
        if row is None:
            return None
        return self._row_to_dealrow(row)

    async def get_pending_approval(self, minutes: int = 5) -> list[DealRow]:
        """Get deals created/updated in last N minutes that haven't been reviewed by admin."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM deals
                WHERE admin_status IS NULL
                AND (created_at::TIMESTAMP > NOW() - MAKE_INTERVAL(mins := $1)
                     OR last_confirmed_at::TIMESTAMP > NOW() - MAKE_INTERVAL(mins := $1))
                ORDER BY score ASC, created_at DESC
                LIMIT 100
                """,
                minutes,
            )
        return [self._row_to_dealrow(row) for row in rows]

    async def mark_reviewed(
        self,
        deal_id: int,
        status: Literal["approved", "rejected"] = "approved",
        user_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        """
        Mark a deal as reviewed by admin or auto-approved by curator.

        Args:
            deal_id: Deal ID to review
            status: 'approved' or 'rejected'
            user_id: Admin user ID (None = auto-approved by curator)
            reason: Optional rejection reason or approval note
        """
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE deals
                SET admin_status = $1, admin_reviewed_by = $2, admin_reviewed_at = $3, admin_review_note = $4
                WHERE id = $5
                """,
                status,
                user_id,
                now,
                reason,
                deal_id,
            )
