from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable

import aiohttp

from stock_notifier.fetch.http_headers import build_request_headers
from stock_notifier.models import AppConfig
from stock_notifier.run_support import redact_url

logger = logging.getLogger(__name__)


class AiohttpFetcher:
    """
    Shared aiohttp session for all HTTP polling jobs.
    One ClientSession per process avoids repeated TLS handshakes.
    """

    def __init__(self, app: AppConfig) -> None:
        self._app = app
        self._session: aiohttp.ClientSession | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._session is None:
                self._session = aiohttp.ClientSession(trust_env=True)

    async def close(self) -> None:
        async with self._lock:
            if self._session is not None:
                await self._session.close()
                self._session = None

    async def get_html(
        self,
        url: str,
        headers_pool: Iterable[dict[str, str]] | None,
        *,
        product_key: str,
        website_key: str,
    ) -> str | None:
        if self._session is None:
            await self.start()
        assert self._session is not None
        headers = build_request_headers(self._app, headers_pool)
        timeout = aiohttp.ClientTimeout(total=120)
        try:
            async with self._session.get(url, headers=headers, timeout=timeout) as response:
                if response.status not in (200, 304):
                    logger.warning(
                        "HTTP %s for %s on %s url=%s",
                        response.status,
                        product_key,
                        website_key,
                        redact_url(url),
                    )
                    if response.status == 404:
                        await asyncio.sleep(60)
                    return None
                return await response.text()
        except asyncio.TimeoutError:
            logger.warning(
                "Timeout fetching %s (%s) url=%s",
                product_key,
                website_key,
                redact_url(url),
            )
            return None
        except aiohttp.ClientError as e:
            logger.warning(
                "Client error %s for %s: %s url=%s",
                website_key,
                product_key,
                e,
                redact_url(url),
            )
            return None
