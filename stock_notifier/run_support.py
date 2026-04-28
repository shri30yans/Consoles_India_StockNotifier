from __future__ import annotations

import asyncio
import random
from urllib.parse import urlparse

from stock_notifier.models import AppConfig


def redact_url(url: str, *, max_path: int = 80) -> str:
    """Log-safe URL: scheme + host + truncated path (no query credentials in path)."""
    try:
        p = urlparse(url)
        path = (p.path or "")[:max_path]
        q = f"?…({len(p.query)} chars)" if p.query else ""
        return f"{p.scheme}://{p.netloc}{path}{q}"
    except Exception:
        return "<invalid-url>"


async def sleep_poll_interval(app: AppConfig, base_seconds: int) -> None:
    """Sleep for one poll cycle with optional jitter from app.fetch."""
    extra = 0.0
    if app.jitter_max_seconds > 0:
        extra = random.uniform(0.0, float(app.jitter_max_seconds))
    await asyncio.sleep(float(base_seconds) + extra)
