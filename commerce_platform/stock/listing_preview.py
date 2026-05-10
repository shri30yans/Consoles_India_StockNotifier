"""Render a retailer listing page once and parse it for preview/admin flows.

Used by the admin tracking-request approval flow to fetch and parse a single
PDP using the same parser registry the workers use, sharing a single Chromium
across requests for the lifetime of the process.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.fetch.factory import create_fetcher
from commerce_platform.platform.fetch.playwright_fetcher import PlaywrightFetcher
from commerce_platform.stock.parsers.protocol import ParseSignal
from commerce_platform.stock.parsers.registry import get_parser_for_source
from commerce_platform.web.retailers import detect_retailer_and_asin


@dataclass(frozen=True)
class ListingScrapeResult:
    ok: bool
    retailer: str | None
    asin: str | None
    fetch_url: str
    reason: str | None = None
    signal: ParseSignal | None = None

    @property
    def name(self) -> str | None:
        return None if self.signal is None else self.signal.listing_title

    @property
    def brand(self) -> str | None:
        return None if self.signal is None else self.signal.listing_brand

    @property
    def image_url(self) -> str | None:
        return None if self.signal is None else self.signal.listing_image_url

    @property
    def price_inr(self) -> float | None:
        return None if self.signal is None else self.signal.price_inr

    @property
    def mrp_inr(self) -> float | None:
        return None if self.signal is None else self.signal.mrp_inr

    @property
    def in_stock(self) -> bool | None:
        return None if self.signal is None else self.signal.in_stock


async def _scrape_with_parser(
    *, retailer: str, fetch_url: str, asin: str | None, config_path: Path, label: str
) -> ListingScrapeResult:
    html_text = await _fetch_listing_html(fetch_url, config_path=config_path, label=label)
    if html_text is None:
        return ListingScrapeResult(
            ok=False,
            retailer=retailer,
            asin=asin,
            fetch_url=fetch_url,
            reason="Could not fetch listing page (blocked, timeout, or invalid response).",
        )
    parser = get_parser_for_source(retailer)
    signal = parser(html_text, fetch_url)
    return ListingScrapeResult(
        ok=True, retailer=retailer, asin=asin, fetch_url=fetch_url, signal=signal
    )


async def scrape_amazon_listing(
    url: str, *, config_path: Path, label: str, asin: str | None
) -> ListingScrapeResult:
    fetch_url = f"https://www.amazon.in/dp/{asin}/" if asin else url.strip()
    return await _scrape_with_parser(
        retailer="amazon", fetch_url=fetch_url, asin=asin, config_path=config_path, label=label
    )


async def scrape_flipkart_listing(
    url: str, *, config_path: Path, label: str, asin: str | None
) -> ListingScrapeResult:
    return await _scrape_with_parser(
        retailer="flipkart",
        fetch_url=url.strip(),
        asin=asin,
        config_path=config_path,
        label=label,
    )


async def scrape_ajio_listing(
    url: str, *, config_path: Path, label: str, asin: str | None
) -> ListingScrapeResult:
    return await _scrape_with_parser(
        retailer="ajio", fetch_url=url.strip(), asin=asin, config_path=config_path, label=label
    )


ScrapeFunc = Callable[[str, Path, str, str | None], Awaitable[ListingScrapeResult]]


async def _dispatch_amazon(
    url: str, config_path: Path, label: str, asin: str | None
) -> ListingScrapeResult:
    return await scrape_amazon_listing(url, config_path=config_path, label=label, asin=asin)


async def _dispatch_flipkart(
    url: str, config_path: Path, label: str, asin: str | None
) -> ListingScrapeResult:
    return await scrape_flipkart_listing(url, config_path=config_path, label=label, asin=asin)


async def _dispatch_ajio(
    url: str, config_path: Path, label: str, asin: str | None
) -> ListingScrapeResult:
    return await scrape_ajio_listing(url, config_path=config_path, label=label, asin=asin)


_SCRAPE_BY_RETAILER: dict[str, ScrapeFunc] = {
    "amazon": _dispatch_amazon,
    "flipkart": _dispatch_flipkart,
    "ajio": _dispatch_ajio,
}


async def scrape_listing(url: str, *, config_path: Path, label: str) -> ListingScrapeResult:
    retailer, asin = detect_retailer_and_asin(url)
    fetch_url = url.strip()
    if retailer is None or retailer not in _SCRAPE_BY_RETAILER:
        return ListingScrapeResult(
            ok=False,
            retailer=retailer,
            asin=asin,
            fetch_url=fetch_url,
            reason="Automatic listing scrape supports Amazon India, Flipkart, and AJIO only.",
        )
    scraper = _SCRAPE_BY_RETAILER[retailer]
    return await scraper(url, config_path, label, asin)


# Module-level shared fetcher: one Chromium serves every admin-preview / listing
# scrape for the lifetime of the process. Launching per request would spawn a
# new browser each time — far too expensive.
_shared_fetcher: PlaywrightFetcher | None = None
_shared_fetcher_lock = asyncio.Lock()


async def _get_shared_fetcher(config_path: Path) -> PlaywrightFetcher:
    global _shared_fetcher
    if _shared_fetcher is not None:
        return _shared_fetcher
    async with _shared_fetcher_lock:
        if _shared_fetcher is None:
            cfg = load(config_path)
            fetcher = create_fetcher(cfg.stock.fetch)
            await fetcher.start()
            _shared_fetcher = fetcher
    return _shared_fetcher


async def _fetch_listing_html(fetch_url: str, *, config_path: Path, label: str) -> str | None:
    fetcher = await _get_shared_fetcher(config_path)
    return await fetcher.get_html(fetch_url, label=label)
