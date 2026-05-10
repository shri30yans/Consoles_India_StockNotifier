"""In-memory deal dedup and per-channel repost cooldown (no SQLite tables)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone


class DealStore:
    """Process-local state only; restarts reset dedup and cooldown windows."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._recorded_fingerprints: set[str] = set()
        self._last_publish: dict[tuple[str, str], datetime] = {}

    async def seen(self, fingerprint: str) -> bool:
        async with self._lock:
            return fingerprint in self._recorded_fingerprints

    async def record_deal(
        self,
        *,
        fingerprint: str,
        product_id: str | None,
        retailer: str,
        url: str,
        price_paise: int,
        score: float,
        category: str,
        source: str,
    ) -> None:
        _ = (product_id, retailer, url, price_paise, score, category, source)
        async with self._lock:
            self._recorded_fingerprints.add(fingerprint)

    async def record_publish(self, fingerprint: str, channel_id: str) -> None:
        async with self._lock:
            self._last_publish[(fingerprint, channel_id)] = datetime.now(timezone.utc)

    async def published_recently(
        self, fingerprint: str, channel_id: str, *, within_hours: int
    ) -> bool:
        since = datetime.now(timezone.utc) - timedelta(hours=within_hours)
        async with self._lock:
            t = self._last_publish.get((fingerprint, channel_id))
            return t is not None and t >= since
