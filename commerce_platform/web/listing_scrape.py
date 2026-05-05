from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.fetch.factory import create_http_fetcher
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


async def scrape_amazon_listing(url: str, *, config_path: Path, label: str, asin: str | None) -> ListingScrapeResult:
    fetch_url = f"https://www.amazon.in/dp/{asin}/" if asin else url.strip()
    html_text = await _fetch_listing_html(fetch_url, config_path=config_path, label=label)
    if html_text is None:
        return ListingScrapeResult(
            ok=False,
            retailer="amazon",
            asin=asin,
            fetch_url=fetch_url,
            reason="Could not fetch listing page (blocked, timeout, or invalid response).",
        )
    parser = get_parser_for_source("amazon")
    signal = parser(html_text, fetch_url)
    return ListingScrapeResult(ok=True, retailer="amazon", asin=asin, fetch_url=fetch_url, signal=signal)


async def scrape_flipkart_listing(url: str, *, config_path: Path, label: str, asin: str | None) -> ListingScrapeResult:
    fetch_url = url.strip()
    html_text = await _fetch_listing_html(fetch_url, config_path=config_path, label=label)
    if html_text is None:
        return ListingScrapeResult(
            ok=False,
            retailer="flipkart",
            asin=asin,
            fetch_url=fetch_url,
            reason="Could not fetch listing page (blocked, timeout, or invalid response).",
        )
    parser = get_parser_for_source("flipkart")
    signal = parser(html_text, fetch_url)
    return ListingScrapeResult(ok=True, retailer="flipkart", asin=asin, fetch_url=fetch_url, signal=signal)


async def scrape_ajio_listing(url: str, *, config_path: Path, label: str, asin: str | None) -> ListingScrapeResult:
    fetch_url = url.strip()
    html_text = await _fetch_listing_html(fetch_url, config_path=config_path, label=label)
    if html_text is None:
        return ListingScrapeResult(
            ok=False,
            retailer="ajio",
            asin=asin,
            fetch_url=fetch_url,
            reason="Could not fetch listing page (blocked, timeout, or invalid response).",
        )
    parser = get_parser_for_source("ajio")
    signal = parser(html_text, fetch_url)
    return ListingScrapeResult(ok=True, retailer="ajio", asin=asin, fetch_url=fetch_url, signal=signal)


ScrapeFunc = Callable[[str, Path, str, str | None], Awaitable[ListingScrapeResult]]


async def _dispatch_amazon(url: str, config_path: Path, label: str, asin: str | None) -> ListingScrapeResult:
    return await scrape_amazon_listing(url, config_path=config_path, label=label, asin=asin)


async def _dispatch_flipkart(url: str, config_path: Path, label: str, asin: str | None) -> ListingScrapeResult:
    return await scrape_flipkart_listing(url, config_path=config_path, label=label, asin=asin)


async def _dispatch_ajio(url: str, config_path: Path, label: str, asin: str | None) -> ListingScrapeResult:
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


async def _fetch_listing_html(fetch_url: str, *, config_path: Path, label: str) -> str | None:
    cfg = load(config_path)
    fetcher = create_http_fetcher(cfg.stock.fetch)
    await fetcher.start()
    try:
        return await fetcher.get_html(fetch_url, label=label)
    finally:
        await fetcher.close()
