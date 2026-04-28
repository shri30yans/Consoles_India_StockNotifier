"""Async SQLAlchemy engine + session factory."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. See .env.example for Supabase format."
        )
    return url


def create_engine() -> AsyncEngine:
    return create_async_engine(
        _database_url(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        echo=False,
    )


def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
