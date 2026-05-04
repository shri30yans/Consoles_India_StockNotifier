from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from commerce_platform.platform.config.schema import StockFetchConfig
from commerce_platform.platform.fetch._headers import random_ua

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

_STEALTH_INIT = """
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined,
  configurable: true,
});
"""


class PlaywrightFetcher:
    def __init__(self, cfg: StockFetchConfig, *, headless: bool = True, channel: str | None = None) -> None:
        self._cfg = cfg
        self._headless = headless
        self._channel = (channel or "").strip() or None
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self) -> None:
        if self._context is not None:
            return
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        launch_kwargs: dict[str, Any] = {"headless": self._headless}
        if self._channel:
            launch_kwargs["channel"] = self._channel
        if self._cfg.playwright_stealth:
            launch_kwargs["args"] = ["--disable-blink-features=AutomationControlled"]
        self._browser = await self._pw.chromium.launch(**launch_kwargs)
        self._context = await self._browser.new_context(
            user_agent=random_ua(self._cfg),
            locale=self._cfg.playwright_locale,
            timezone_id=self._cfg.playwright_timezone_id,
            viewport={"width": 1920, "height": 1080},
        )
        if self._cfg.playwright_stealth:
            await self._context.add_init_script(_STEALTH_INIT)

    async def close(self) -> None:
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()
            self._pw = None

    async def new_page(self) -> Page:
        await self.start()
        assert self._context is not None
        return await self._context.new_page()

    async def get_html(self, url: str, *, label: str = "") -> str | None:
        page = await self.new_page()
        try:
            return await self._fetch_page(page, url, label=label)
        finally:
            await page.close()

    async def _fetch_page(self, page: Page, url: str, *, label: str = "") -> str | None:
        try:
            response = await page.goto(url, timeout=120_000)
            if response is None:
                logger.warning("No response for %s", label or url)
                return None
            if response.status not in (200, 304):
                logger.warning("HTTP %s for %s", response.status, label or url)
                if response.status == 404:
                    await asyncio.sleep(60)
                return None
            return await page.content()
        except asyncio.TimeoutError:
            logger.warning("Playwright timeout for %s", label or url)
            return None


class PlaywrightPageFetcher:
    """Long-lived page fetcher — reuses the same Page across calls (stock polling)."""

    def __init__(self, fetcher: PlaywrightFetcher) -> None:
        self._fetcher = fetcher
        self._page: Page | None = None

    async def start(self) -> None:
        await self._fetcher.start()
        self._page = await self._fetcher.new_page()

    async def close(self) -> None:
        if self._page:
            await self._page.close()
            self._page = None

    async def get_html(self, url: str, *, label: str = "") -> str | None:
        if self._page is None:
            await self.start()
        assert self._page is not None
        return await self._fetcher._fetch_page(self._page, url, label=label)
