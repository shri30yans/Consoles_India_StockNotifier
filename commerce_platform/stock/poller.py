"""Poller — fetch a product URL, parse it, emit price observation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from commerce_platform.platform.config.schema import ProductConfig, WatchConfig
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.events.observation import PriceObservation
from commerce_platform.platform.fetch.protocol import HtmlFetcher
from commerce_platform.stock.parsers import ajio as ajio_parser
from commerce_platform.stock.parsers import amazon as amazon_parser
from commerce_platform.stock.parsers import flipkart as flipkart_parser

logger = logging.getLogger(__name__)

_PARSERS = {
    "amazon": amazon_parser.parse,
    "flipkart": flipkart_parser.parse,
    "ajio": ajio_parser.parse,
}


def _parser_key(source: str) -> str:
    """Map watch.source (e.g. ajio_playwright) to registered parser name."""
    if source.endswith("_playwright"):
        return source[: -len("_playwright")]
    return source


class Poller:
    def __init__(
        self,
        fetcher: HtmlFetcher,
        bus: EventBus,
    ) -> None:
        self._fetcher = fetcher
        self._bus = bus

    async def poll(self, product: ProductConfig, watch: WatchConfig) -> None:
        label = f"{product.id}@{watch.source}"
        html = await self._fetcher.get_html(watch.url, label=label)
        if html is None:
            logger.warning("Scrape failed — no HTML for %s (network/block/captcha?)", label)
            return

        logger.info("Scrape fetch OK for %s — %d byte(s) HTML", label, len(html))

        parser = _PARSERS.get(_parser_key(watch.source))
        if parser is None:
            logger.warning("No parser for source %s", watch.source)
            return

        signal = parser(html, watch.url)

        logger.info(
            "Scraped %s: in_stock=%s price_inr=%s mrp_inr=%s method=%s",
            label,
            signal.in_stock,
            signal.price_inr,
            signal.mrp_inr,
            signal.method or "—",
        )

        # Create observation
        observation = PriceObservation(
            product_id=product.id,
            retailer=watch.source,
            price_paise=int(signal.price_inr * 100) if signal.price_inr else 0,
            mrp_paise=int(signal.mrp_inr * 100) if signal.mrp_inr else None,
            in_stock=signal.in_stock,
            source=f"scraper:{watch.source}",
            observed_at=datetime.now(timezone.utc).isoformat(),
            product_url=watch.url,
            product_title=product.name,
        )

        # Emit observation
        await self._bus.publish(observation)
