"""Shared header building logic for all fetchers."""

from __future__ import annotations

import random

from commerce_platform.platform.config.schema import StockFetchConfig

_FALLBACK_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

_ua_instance = None


def _ua() -> object:
    global _ua_instance
    if _ua_instance is None:
        from fake_useragent import UserAgent
        _ua_instance = UserAgent()
    return _ua_instance


def random_ua(cfg: StockFetchConfig) -> str:
    if cfg.use_fake_useragent:
        try:
            ua = _ua()
            s = ua.random  # type: ignore[attr-defined]
            if isinstance(s, str) and s.strip():
                return s.strip()
        except Exception:
            pass
    return random.choice(_FALLBACK_UAS)


def random_headers(cfg: StockFetchConfig) -> dict[str, str]:
    return {
        "User-Agent": random_ua(cfg),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
