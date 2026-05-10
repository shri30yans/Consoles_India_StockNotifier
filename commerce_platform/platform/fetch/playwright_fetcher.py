"""Playwright fetcher — one persistent Chromium powering both fast HTTP fetches
and full JS-rendered page fetches.

Two methods:
  - ``get_html(url)`` — uses ``BrowserContext.request`` (real Chromium HTTP stack,
    real Chrome TLS / JA3 fingerprint, shared cookies). No DOM, no JS. Use for
    static HTML pages (most retailer PDPs).
  - ``get_html_rendered(url)`` — opens a Page, navigates with
    ``wait_until="domcontentloaded"`` then waits briefly for network to settle.
    Use only for SPA / JS-rendered listings (Amazon /deals, Flipkart SERP, etc.).

Both share one Browser + one BrowserContext, so cookies, storage_state, TLS, and
proxy settings are identical across modes. A single Chromium process is launched
on first use and torn down on ``close()``.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.async_api import (
    async_playwright,
)

from commerce_platform.platform.config.schema import StockFetchConfig
from commerce_platform.platform.fetch._headers import random_profile

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Playwright, Route

logger = logging.getLogger(__name__)

_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined, configurable: true});
"""

# Resource types we never need for HTML scraping. Blocking them on the rendered
# path cuts page weight ~70-80% and speeds up domcontentloaded proportionally.
_BLOCKED_RESOURCE_TYPES = frozenset({"image", "media", "font", "stylesheet"})


async def _launch_browser(
    cfg: StockFetchConfig,
    *,
    headless: bool = True,
    channel: str | None = None,
) -> tuple[Playwright, Browser, BrowserContext] | None:
    try:
        profile = random_profile()
        state_path = Path(cfg.playwright_state_file) if cfg.playwright_state_file else None

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=headless,
            channel=(channel or "").strip() or None,
            args=["--disable-blink-features=AutomationControlled"] if cfg.playwright_stealth else [],
        )

        ctx_kwargs: dict = dict(
            user_agent=profile["ua"],
            locale=cfg.playwright_locale,
            timezone_id=cfg.playwright_timezone_id,
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={"Accept-Language": profile["accept_language"]},
        )
        if state_path and state_path.exists():
            ctx_kwargs["storage_state"] = str(state_path)
            logger.debug("Loaded browser state from %s", state_path)

        context = await browser.new_context(**ctx_kwargs)

        if cfg.playwright_stealth:
            await context.add_init_script(_STEALTH_SCRIPT)

        return pw, browser, context
    except NotImplementedError:
        logger.warning("Playwright unavailable on this platform")
        return None


async def _block_subresources(route: Route) -> None:
    if route.request.resource_type in _BLOCKED_RESOURCE_TYPES:
        await route.abort()
    else:
        await route.continue_()


class PlaywrightFetcher:
    """Unified Chromium-backed fetcher: fast HTTP via APIRequestContext, plus an
    on-demand rendered-page mode for JS-heavy listings."""

    def __init__(
        self,
        cfg: StockFetchConfig,
        *,
        headless: bool = True,
        channel: str | None = None,
    ) -> None:
        self._cfg = cfg
        self._headless = headless
        self._channel = channel
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._available = True
        self._start_lock = asyncio.Lock()
        self._route_attached = False

    async def start(self) -> None:
        if self._context is not None or not self._available:
            return
        async with self._start_lock:
            if self._context is not None or not self._available:
                return
            result = await _launch_browser(self._cfg, headless=self._headless, channel=self._channel)
            if result is None:
                self._available = False
                return
            self._pw, self._browser, self._context = result
            # Routes apply only to Page navigation traffic (not to context.request),
            # so we can attach once and let it cover every rendered fetch.
            await self._context.route("**/*", _block_subresources)
            self._route_attached = True

    async def save_state(self) -> None:
        """Persist cookies + localStorage to ``playwright_state_file`` if configured."""
        if self._context is None or not self._cfg.playwright_state_file:
            return
        path = Path(self._cfg.playwright_state_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=str(path))
        logger.info("Browser state saved to %s", path)

    async def close(self) -> None:
        await self.save_state()
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()
            self._pw = None
        self._route_attached = False

    async def get_html(self, url: str, *, label: str = "") -> str | None:
        """Fast path: real Chrome TLS + cookie jar, no DOM/JS."""
        await self.start()
        if self._context is None:
            return None
        try:
            response = await self._context.request.get(url, timeout=30_000)
        except PlaywrightTimeoutError:
            logger.warning("Request timeout for %s", label or url)
            return None
        except PlaywrightError as e:
            logger.warning("Request error for %s: %s", label or url, e)
            return None

        if response.status not in (200, 304):
            logger.warning("HTTP %s for %s", response.status, label or url)
            if response.status == 404:
                await asyncio.sleep(60)
            return None
        try:
            return await response.text()
        except PlaywrightError as e:
            logger.warning("Body decode failed for %s: %s", label or url, e)
            return None

    async def get_html_rendered(self, url: str, *, label: str = "") -> str | None:
        """Slow path: full Chromium render. Use only for JS-rendered pages."""
        await self.start()
        if self._context is None:
            return None

        page = await self._context.new_page()
        try:
            try:
                response = await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
            except PlaywrightTimeoutError:
                logger.debug("domcontentloaded timeout for %s", label or url)
                return None

            if response is None:
                logger.warning("No response for %s", label or url)
                return None
            if response.status not in (200, 304):
                logger.warning("HTTP %s for %s", response.status, label or url)
                if response.status == 404:
                    await asyncio.sleep(60)
                return None

            # Give the React tree a brief window to mount and finish XHRs.
            try:
                await page.wait_for_load_state("networkidle", timeout=8_000)
            except PlaywrightTimeoutError:
                pass  # networkidle is best-effort; SPAs with poll loops never reach it.

            return await page.content()
        finally:
            await page.close()
