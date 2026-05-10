"""One fetcher to rule them all — a Chromium-backed PlaywrightFetcher.

Static HTML callers use ``fetcher.get_html(...)``; SPA/JS-rendered callers use
``fetcher.get_html_rendered(...)``. Both share the same Browser, BrowserContext,
cookie jar, and TLS fingerprint.
"""

from __future__ import annotations

from commerce_platform.platform.config.schema import StockFetchConfig
from commerce_platform.platform.fetch.playwright_fetcher import PlaywrightFetcher


def create_fetcher(cfg: StockFetchConfig, *, headless: bool = True) -> PlaywrightFetcher:
    return PlaywrightFetcher(cfg, headless=headless)
