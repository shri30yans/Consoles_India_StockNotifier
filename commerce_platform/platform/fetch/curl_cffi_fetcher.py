from __future__ import annotations

import asyncio
import logging
import random
from typing import TYPE_CHECKING

from commerce_platform.platform.config.schema import StockFetchConfig
from commerce_platform.platform.fetch._headers import random_headers

if TYPE_CHECKING:
    from curl_cffi.requests import AsyncSession

logger = logging.getLogger(__name__)


class CurlCffiFetcher:
    def __init__(self, cfg: StockFetchConfig) -> None:
        self._cfg = cfg
        self._session: AsyncSession | None = None
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

    async def get_html(self, url: str, *, label: str = "") -> str | None:
        await self.start()
        assert self._session is not None
        if self._cfg.jitter_max_seconds > 0:
            await asyncio.sleep(random.uniform(0, self._cfg.jitter_max_seconds))
        try:
            response = await self._session.get(
                url,
                headers=random_headers(self._cfg),
                impersonate=self._cfg.curl_impersonate,
                timeout=120,
            )
            if response.status_code not in (200, 304):
                logger.warning("HTTP %s fetching %s", response.status_code, label or url)
                if response.status_code == 404:
                    await asyncio.sleep(60)
                return None
            return response.text
        except asyncio.TimeoutError:
            logger.warning("Timeout fetching %s", label or url)
            return None
        except Exception as e:
            logger.warning("curl_cffi error fetching %s: %s", label or url, e)
            return None
