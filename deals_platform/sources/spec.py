from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WatchSpec:
    """A single (retailer, url) target the platform watches."""

    retailer: str
    url: str
    poll_seconds: int = 600
    title_hint: str | None = None
