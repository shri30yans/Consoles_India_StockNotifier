from __future__ import annotations

from commerce_platform.platform.config.schema import StockFetchConfig
from commerce_platform.platform.fetch.aiohttp_fetcher import AiohttpFetcher
from commerce_platform.platform.fetch.curl_cffi_fetcher import CurlCffiFetcher
from commerce_platform.platform.fetch.playwright_fetcher import PlaywrightFetcher
from commerce_platform.platform.fetch.protocol import HtmlFetcher


def create_http_fetcher(cfg: StockFetchConfig) -> HtmlFetcher:
    if cfg.http_client == "curl_cffi":
        return CurlCffiFetcher(cfg)
    return AiohttpFetcher(cfg)


def create_playwright_fetcher(cfg: StockFetchConfig, *, headless: bool = True) -> PlaywrightFetcher:
    return PlaywrightFetcher(cfg, headless=headless)
