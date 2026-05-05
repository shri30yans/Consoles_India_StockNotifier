"""Poller — fetch a product URL, parse it, emit price observation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from commerce_platform.platform.config.schema import ProductConfig, WatchConfig
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.events.observation import PriceObservation
from commerce_platform.platform.fetch.protocol import HtmlFetcher
from commerce_platform.stock.parsers.registry import get_parser_for_source

logger = logging.getLogger(__name__)


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

        try:
            parser = get_parser_for_source(watch.source)
        except ValueError:
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
            product_title=signal.listing_title or product.name,
        )

        # Emit observation
        await self._bus.publish(observation)
