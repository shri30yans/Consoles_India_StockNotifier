"""Dev convenience: create all tables. In prod, prefer Alembic migrations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from deals_platform.storage.schema import Base


async def create_all(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
