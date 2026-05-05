"""Config settings repository — DB-backed admin-editable configuration."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class ConfigSettingsRepo:
    """Read and write global configuration to DB (replaces YAML writes from admin)."""

    def __init__(self, pool: asyncpg.pool.Pool) -> None:
        self._pool = pool

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a config value. Returns default if key not found."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM config_settings WHERE key = $1", key)
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to decode config value for key=%s", key)
            return default

    async def set(self, key: str, value: Any) -> None:
        """Set a config value (overwrites if exists)."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO config_settings (key, value, updated_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = $3
                """,
                key,
                json.dumps(value),
                datetime.now(timezone.utc).isoformat(),
            )

    async def get_all_prefixed(self, prefix: str) -> dict[str, Any]:
        """Get all config values whose key starts with prefix."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT key, value FROM config_settings WHERE key LIKE $1",
                f"{prefix}%",
            )
        result = {}
        for row in rows:
            try:
                result[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to decode config value for key=%s", row["key"])
        return result

    async def delete(self, key: str) -> None:
        """Delete a config value."""
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM config_settings WHERE key = $1", key)
