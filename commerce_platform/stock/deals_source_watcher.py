"""Platform source watcher for retailer SERP deal candidates."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from commerce_platform.platform.config.schema import PlatformSourceConfig
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.events.observation import PriceObservation
from commerce_platform.platform.fetch.protocol import HtmlFetcher
from commerce_platform.platform.store.repos import CatalogRepo
from commerce_platform.stock.parsers.registry import get_parser_for_source
from commerce_platform.stock.sources.serp_parsers import (
    extract_ajio_serp_urls,
    extract_amazon_serp_urls,
    extract_flipkart_serp_urls,
)
from commerce_platform.web.retailers import detect_retailer_and_asin

logger = logging.getLogger(__name__)


class DealsSourceWatcher:
    def __init__(
        self,
        source: PlatformSourceConfig,
        fetcher: HtmlFetcher,
        catalog_repo: CatalogRepo,
        bus: EventBus,
    ) -> None:
        self._source = source
        self._fetcher = fetcher
        self._catalog_repo = catalog_repo
        self._bus = bus

    async def run(self) -> None:
        seed_urls = [u for u in (self._source.seed_urls or []) if u.strip()]
        if not seed_urls and self._source.url:
            seed_urls = [self._source.url.strip()]
        if not seed_urls:
            logger.warning("%s source has no url/seed_urls configured", self._source.type)
            return

        logger.info(
            "Deals source watcher started: type=%s seeds=%d every=%ds",
            self._source.type,
            len(seed_urls),
            self._source.poll_seconds,
        )
        backoff = 1.0
        while True:
            try:
                for seed in seed_urls:
                    await self._poll_seed(seed)
                backoff = 1.0
            except Exception:
                logger.exception("Deals source poll error type=%s", self._source.type)
                await asyncio.sleep(min(backoff * 2, 300))
                backoff = min(backoff * 2, 300)
                continue
            await asyncio.sleep(self._source.poll_seconds)

    async def _poll_seed(self, seed_url: str) -> None:
        html = await self._fetcher.get_html(seed_url, label=f"{self._source.type}:seed")
        if html is None:
            logger.warning("Deals source fetch failed type=%s seed=%s", self._source.type, seed_url)
            return

        candidates = _extract_candidates(self._source.type, html, max_links=max(1, self._source.max_links_per_seed))
        logger.info(
            "Deals source parsed candidates: type=%s seed=%s count=%d",
            self._source.type,
            seed_url,
            len(candidates),
        )
        for url in candidates:
            await self._process_candidate(url)

    async def _process_candidate(self, url: str) -> None:
        retailer, sku = detect_retailer_and_asin(url)
        if not retailer:
            return

        product_id: str | None = None
        if sku:
            product_id = await self._catalog_repo.get_product_id_by_retailer_sku(retailer, sku)
        if product_id is None:
            product_id = await self._catalog_repo.get_product_id_by_watch_url(url)
        if product_id is None:
            return

        html = await self._fetcher.get_html(url, label=f"{self._source.type}:{product_id}")
        if html is None:
            return

        parser = get_parser_for_source(retailer)
        signal = parser(html, url)

        observation = PriceObservation(
            product_id=product_id,
            retailer=retailer,
            price_paise=int(signal.price_inr * 100) if signal.price_inr else 0,
            mrp_paise=int(signal.mrp_inr * 100) if signal.mrp_inr else None,
            in_stock=signal.in_stock,
            source=f"platform:{self._source.type}",
            observed_at=datetime.now(timezone.utc).isoformat(),
            product_url=url,
            product_title=signal.listing_title or product_id,
        )
        await self._bus.publish(observation)


def _extract_candidates(source_type: str, page_html: str, *, max_links: int) -> list[str]:
    if source_type == "amazon_serp":
        return extract_amazon_serp_urls(page_html, max_links=max_links)
    if source_type == "flipkart_serp":
        return extract_flipkart_serp_urls(page_html, max_links=max_links)
    if source_type == "ajio_serp":
        return extract_ajio_serp_urls(page_html, max_links=max_links)
    return []
