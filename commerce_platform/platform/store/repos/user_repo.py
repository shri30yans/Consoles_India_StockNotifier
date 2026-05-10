"""User repository — admin users and authentication."""

from __future__ import annotations

from typing import NamedTuple

import asyncpg


class UserRow(NamedTuple):
    """A user from app_users table."""

    id: int
    email: str
    password_hash: str
    role: str
    created_at: str


class UserRepo:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, email: str, password_hash: str, *, role: str = "user") -> int:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO app_users (email, password_hash, role, created_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                email.lower().strip(),
                password_hash,
                role,
                now,
            )
        return int(row["id"])

    async def get_by_email(self, email: str) -> UserRow | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, password_hash, role, created_at FROM app_users WHERE email = $1",
                email.lower().strip(),
            )
        if row is None:
            return None
        return UserRow(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            created_at=row["created_at"],
        )

    async def get_by_id(self, user_id: int) -> UserRow | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, password_hash, role, created_at FROM app_users WHERE id = $1",
                user_id,
            )
        if row is None:
            return None
        return UserRow(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            created_at=row["created_at"],
        )

    async def count(self) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM app_users")
        return row["cnt"] if row else 0
