"""Tracking request repository — admin approval workflow for new products."""

from __future__ import annotations

from typing import NamedTuple

import asyncpg


class TrackingRow(NamedTuple):
    """A tracking request row."""

    id: int
    user_id: int
    raw_url: str
    normalized_retailer_hint: str | None
    desired_product_name: str | None
    note: str | None
    status: str
    admin_note: str | None
    created_at: str
    decided_at: str | None
    decided_by: int | None
    promoted_product_id: str | None


class TrackingRepo:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        user_id: int,
        raw_url: str,
        retailer_hint: str | None,
        desired_product_name: str | None,
        note: str | None,
    ) -> int:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO tracking_requests (user_id, raw_url, normalized_retailer_hint, desired_product_name, note, status, created_at)
                VALUES ($1, $2, $3, $4, $5, 'pending', $6)
                RETURNING id
                """,
                user_id,
                raw_url,
                retailer_hint,
                desired_product_name,
                note,
                now,
            )
        return int(row["id"])

    async def list_for_user(self, user_id: int) -> list[TrackingRow]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, raw_url, normalized_retailer_hint, desired_product_name, note,
                       status, admin_note, created_at, decided_at, decided_by, promoted_product_id
                FROM tracking_requests
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id,
            )
        return [self._row_to_tracking(r) for r in rows]

    async def list_by_status(self, status: str | None) -> list[TrackingRow]:
        async with self._pool.acquire() as conn:
            if status is None:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, raw_url, normalized_retailer_hint, desired_product_name, note,
                           status, admin_note, created_at, decided_at, decided_by, promoted_product_id
                    FROM tracking_requests
                    ORDER BY created_at DESC
                    """
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, raw_url, normalized_retailer_hint, desired_product_name, note,
                           status, admin_note, created_at, decided_at, decided_by, promoted_product_id
                    FROM tracking_requests
                    WHERE status = $1
                    ORDER BY created_at DESC
                    """,
                    status,
                )
        return [self._row_to_tracking(r) for r in rows]

    async def get(self, request_id: int) -> TrackingRow | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, raw_url, normalized_retailer_hint, desired_product_name, note,
                       status, admin_note, created_at, decided_at, decided_by, promoted_product_id
                FROM tracking_requests
                WHERE id = $1
                """,
                request_id,
            )
        if row is None:
            return None
        return self._row_to_tracking(row)

    async def set_rejected(self, request_id: int, admin_id: int, admin_note: str) -> bool:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE tracking_requests
                SET status = 'rejected', admin_note = $1, decided_at = $2, decided_by = $3
                WHERE id = $4 AND status = 'pending'
                """,
                admin_note,
                now,
                admin_id,
                request_id,
            )
        return "0" not in str(result)

    async def set_approved_and_promote(
        self, request_id: int, admin_id: int, admin_note: str, promoted_product_id: str
    ) -> bool:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE tracking_requests
                SET status = 'approved', admin_note = $1, decided_at = $2, decided_by = $3, promoted_product_id = $4
                WHERE id = $5 AND status = 'pending'
                """,
                admin_note,
                now,
                admin_id,
                promoted_product_id,
                request_id,
            )
        return "0" not in str(result)

    @staticmethod
    def _row_to_tracking(row: asyncpg.Record) -> TrackingRow:
        return TrackingRow(
            id=row["id"],
            user_id=row["user_id"],
            raw_url=row["raw_url"],
            normalized_retailer_hint=row["normalized_retailer_hint"],
            desired_product_name=row["desired_product_name"],
            note=row["note"],
            status=row["status"],
            admin_note=row["admin_note"],
            created_at=row["created_at"],
            decided_at=row["decided_at"],
            decided_by=row["decided_by"],
            promoted_product_id=row["promoted_product_id"],
        )
