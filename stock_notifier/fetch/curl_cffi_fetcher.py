from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING

from stock_notifier.fetch.http_headers import build_request_headers
from stock_notifier.models import AppConfig
from stock_notifier.run_support import redact_url

if TYPE_CHECKING:
    from curl_cffi.requests import AsyncSession as CurlAsyncSession

logger = logging.getLogger(__name__)


class CurlCffiFetcher:
    """
    TLS/HTTP fingerprint-aware fetcher (curl_cffi impersonate profile).
    Prefer when aiohttp is blocked but a real browser fingerprint works.
    """

    def __init__(self, app: AppConfig) -> None:
        self._app = app
        self._session: CurlAsyncSession | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._session is None:
                from curl_cffi.requests import AsyncSession

                self._session = AsyncSession()

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
        await self.start()
        assert self._session is not None
        headers = build_request_headers(self._app, headers_pool)
        try:
            response = await self._session.get(
                url,
                headers=headers,
                impersonate=self._app.curl_impersonate,
                timeout=120,
            )
            if response.status_code not in (200, 304):
                logger.warning(
                    "HTTP %s for %s on %s url=%s",
                    response.status_code,
                    product_key,
                    website_key,
                    redact_url(url),
                )
                if response.status_code == 404:
                    await asyncio.sleep(60)
                return None
            return response.text
        except asyncio.TimeoutError:
            logger.warning(
                "Timeout fetching %s (%s) url=%s",
                product_key,
                website_key,
                redact_url(url),
            )
            return None
        except Exception as e:
            logger.warning(
                "curl_cffi error %s for %s: %s url=%s",
                website_key,
                product_key,
                e,
                redact_url(url),
            )
            return None
