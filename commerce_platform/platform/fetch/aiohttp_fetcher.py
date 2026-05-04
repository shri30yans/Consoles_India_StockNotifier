from __future__ import annotations

import asyncio
import logging
import random

import aiohttp

from commerce_platform.platform.config.schema import StockFetchConfig
from commerce_platform.platform.fetch._headers import random_headers

logger = logging.getLogger(__name__)


class AiohttpFetcher:
    def __init__(self, cfg: StockFetchConfig) -> None:
        self._cfg = cfg
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

    async def get_html(self, url: str, *, label: str = "") -> str | None:
        if self._session is None:
            await self.start()
        assert self._session is not None
        if self._cfg.jitter_max_seconds > 0:
            await asyncio.sleep(random.uniform(0, self._cfg.jitter_max_seconds))
        timeout = aiohttp.ClientTimeout(total=120)
        try:
            async with self._session.get(
                url, headers=random_headers(self._cfg), timeout=timeout
            ) as resp:
                if resp.status not in (200, 304):
                    logger.warning("HTTP %s fetching %s", resp.status, label or url)
                    if resp.status == 404:
                        await asyncio.sleep(60)
                    return None
                return await resp.text()
        except asyncio.TimeoutError:
            logger.warning("Timeout fetching %s", label or url)
            return None
        except aiohttp.ClientError as e:
            logger.warning("Client error fetching %s: %s", label or url, e)
            return None
