from __future__ import annotations

from stock_notifier.fetch.aiohttp_fetcher import AiohttpFetcher
from stock_notifier.fetch.curl_cffi_fetcher import CurlCffiFetcher
from stock_notifier.fetch.html_fetcher import HtmlFetcher
from stock_notifier.models import AppConfig


def create_requests_fetcher(app: AppConfig) -> HtmlFetcher:
    if app.http_client == "curl_cffi":
        return CurlCffiFetcher(app)
    if app.http_client == "aiohttp":
        return AiohttpFetcher(app)
    raise ValueError(f"Unknown http_client: {app.http_client!r}")
