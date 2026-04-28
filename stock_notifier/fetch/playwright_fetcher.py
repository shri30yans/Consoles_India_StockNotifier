from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from stock_notifier.fetch.http_headers import default_browser_user_agent, playwright_extra_headers
from stock_notifier.fetch.playwright_stealth import PLAYWRIGHT_STEALTH_INIT
from stock_notifier.models import AppConfig

logger = logging.getLogger(__name__)


class PlaywrightFetcher:
    """Shared Chromium context; each job keeps one Page for the polling loop."""

    def __init__(self, app: AppConfig) -> None:
        self._app = app
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self) -> None:
        if self._browser is not None:
            return
        self._pw = await async_playwright().start()
        launch_kwargs: dict = {"headless": True}
        if self._app.playwright_apply_stealth:
            launch_kwargs["args"] = ["--disable-blink-features=AutomationControlled"]
        self._browser = await self._pw.chromium.launch(**launch_kwargs)
        self._context = await self._browser.new_context(
            user_agent=default_browser_user_agent(self._app),
            locale=self._app.playwright_locale,
            timezone_id=self._app.playwright_timezone_id,
            viewport={"width": 1920, "height": 1080},
            color_scheme="light",
        )
        if self._app.playwright_apply_stealth:
            await self._context.add_init_script(PLAYWRIGHT_STEALTH_INIT)

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._pw is not None:
            await self._pw.stop()
            self._pw = None

    async def new_page(self) -> Page:
        await self.start()
        assert self._context is not None
        return await self._context.new_page()

    async def fetch_in_page(
        self,
        page: Page,
        url: str,
        headers_pool: Iterable[dict[str, str]] | None,
        *,
        product_key: str,
        website_key: str,
    ) -> str | None:
        headers = playwright_extra_headers(self._app, headers_pool)
        try:
            await page.set_extra_http_headers(headers)
            response = await page.goto(url, timeout=120_000)
            if response is None:
                logger.warning("No response for %s on %s", product_key, website_key)
                return None
            if response.status not in (200, 304):
                logger.warning(
                    "HTTP %s for %s on %s",
                    response.status,
                    product_key,
                    website_key,
                )
                if response.status == 404:
                    await asyncio.sleep(60)
                return None
            return await page.content()
        except asyncio.TimeoutError:
            logger.warning("Playwright timeout %s (%s)", product_key, website_key)
            return None
