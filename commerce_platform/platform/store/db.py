"""PostgreSQL connection pool via asyncpg."""

from __future__ import annotations

import logging
import os
import socket
from typing import Any
from urllib.parse import urlparse

from commerce_platform.platform.config.schema import StoreConfig
from commerce_platform.platform.store.sql_compat import (
    normalize_dsn_for_asyncpg,
    postgres_ssl_from_env,
    redact_dsn_for_logs,
    strip_ssl_related_query_params,
)

logger = logging.getLogger(__name__)


class Database:
    """Opened with ``await db.open()`` — exposes ``db.pool`` for queries."""

    def __init__(self, store: StoreConfig) -> None:
        self._store = store
        self._pg_pool: Any | None = None

    def describe_for_logs(self) -> str:
        return redact_dsn_for_logs(self.effective_dsn())

    def effective_dsn(self) -> str:
        raw = (self._store.dsn or "").strip()
        if raw:
            return normalize_dsn_for_asyncpg(raw)
        env = os.getenv("DATABASE_URL", "").strip()
        if not env:
            raise RuntimeError(
                "No Postgres DSN: set platform.store.dsn or DATABASE_URL in the environment."
            )
        return normalize_dsn_for_asyncpg(env)

    async def open(self) -> None:
        import asyncpg

        dsn = self.effective_dsn()
        ssl_arg = postgres_ssl_from_env()
        if ssl_arg is False:
            dsn = strip_ssl_related_query_params(dsn)
        try:
            self._pg_pool = await asyncpg.create_pool(dsn, ssl=ssl_arg, min_size=1, max_size=10)
        except socket.gaierror as e:
            host = urlparse(dsn).hostname or "?"
            raise RuntimeError(
                f"Database host {host!r} could not be resolved ({e}). "
                "Copy the URI from Supabase → Project Settings → Database; "
                "the segment in db.<project-ref>.supabase.co must match your project reference exactly."
            ) from e
        logger.info("Database pool opened: %s", self.describe_for_logs())

    async def close(self) -> None:
        if self._pg_pool is not None:
            await self._pg_pool.close()
            self._pg_pool = None
            logger.info("Database pool closed")

    @property
    def pool(self) -> Any:
        assert self._pg_pool is not None, "Database not opened"
        return self._pg_pool
