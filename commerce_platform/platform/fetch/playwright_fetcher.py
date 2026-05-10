"""Browser automation fetcher using Playwright — for JS-heavy pages."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright
from commerce_platform.platform.config.schema import StockFetchConfig
from commerce_platform.platform.fetch._headers import random_ua

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined,
  configurable: true,
});
"""


async def _launch_browser(cfg: StockFetchConfig, *, headless: bool = True, channel: str | None = None) -> tuple[Playwright, Browser, BrowserContext] | None:
    """Launch Playwright browser and context, or return None if unavailable."""
    try:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=headless,
            channel=(channel or "").strip() or None,
            args=["--disable-blink-features=AutomationControlled"] if cfg.playwright_stealth else None,
        )
        context = await browser.new_context(
            user_agent=random_ua(cfg),
            locale=cfg.playwright_locale,
            timezone_id=cfg.playwright_timezone_id,
            viewport={"width": 1920, "height": 1080},
        )
        if cfg.playwright_stealth:
            await context.add_init_script(_STEALTH_SCRIPT)
        return pw, browser, context
    except NotImplementedError:
        logger.warning("Playwright unavailable — asyncio subprocess not supported on this platform")
        return None


class PlaywrightFetcher:
    """Fetcher using Playwright for JavaScript rendering."""

    def __init__(self, cfg: StockFetchConfig, *, headless: bool = True, channel: str | None = None) -> None:
        self._cfg = cfg
        self._headless = headless
        self._channel = channel
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._available = True

    async def start(self) -> None:
        """Initialize browser. Silent no-op if already initialized or unavailable."""
        if self._context is not None or not self._available:
            return
        result = await _launch_browser(self._cfg, headless=self._headless, channel=self._channel)
        if result is None:
            self._available = False
            return
        self._pw, self._browser, self._context = result

    async def close(self) -> None:
        """Clean up browser resources."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()
            self._pw = None

    async def get_html(self, url: str, *, label: str = "") -> str | None:
        """Fetch URL via Playwright, or return None if unavailable."""
        await self.start()
        if self._context is None:
            return None

        page = await self._context.new_page()
        try:
            response = await page.goto(url, timeout=120_000)
            if response is None or response.status not in (200, 304):
                if response:
                    logger.warning("HTTP %s for %s", response.status, label or url)
                    if response.status == 404:
                        await asyncio.sleep(60)
                else:
                    logger.warning("No response for %s", label or url)
                return None
            return await page.content()
        except asyncio.TimeoutError:
            logger.warning("Playwright timeout for %s", label or url)
            return None
        finally:
            await page.close()


class PlaywrightPageFetcher:
    """Reusable page fetcher — maintains a single page for repeated requests."""

    def __init__(self, fetcher: PlaywrightFetcher) -> None:
        self._fetcher = fetcher
        self._page: Page | None = None

    async def start(self) -> None:
        """Initialize page."""
        await self._fetcher.start()
        if self._fetcher._context is None:
            return
        self._page = await self._fetcher._context.new_page()

    async def close(self) -> None:
        """Clean up page."""
        if self._page:
            await self._page.close()
            self._page = None

    async def get_html(self, url: str, *, label: str = "") -> str | None:
        """Fetch URL via existing page."""
        if self._page is None:
            await self.start()
        if self._page is None:
            return None

        try:
            response = await self._page.goto(url, timeout=120_000)
            if response is None or response.status not in (200, 304):
                if response:
                    logger.warning("HTTP %s for %s", response.status, label or url)
                else:
                    logger.warning("No response for %s", label or url)
                return None
            return await self._page.content()
        except asyncio.TimeoutError:
            logger.warning("Playwright timeout for %s", label or url)
            return None
