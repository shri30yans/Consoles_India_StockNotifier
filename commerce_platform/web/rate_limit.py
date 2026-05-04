"""Simple per-key sliding-window rate limiter."""

from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_per_hour: int) -> None:
        self._max = max_per_hour
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.time()
        cutoff = now - 3600.0
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]
        if len(self._hits[key]) >= self._max:
            return False
        self._hits[key].append(now)
        return True
