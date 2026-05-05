"""Deal discovery from retailer pages — main watcher for deal-centric sources."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from commerce_platform.deals.scorer import DealScorer
from commerce_platform.platform.config.schema import PlatformSourceConfig
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.events.observation import PriceObservation
from commerce_platform.platform.fetch.protocol import HtmlFetcher
from commerce_platform.platform.store.repos import CatalogRepo, DealRepo
from commerce_platform.stock.sources.serp_parsers import (
    ListingItem,
    extract_ajio_offer_items,
    extract_amazon_deal_items,
    extract_flipkart_offer_items,
    extract_myntra_offer_items,
)
from commerce_platform.stock.sources.serp_parsers import (
    extract_amazon_serp_urls,
    extract_ajio_serp_urls,
    extract_flipkart_serp_urls,
)
from commerce_platform.stock.parsers.registry import get_parser_for_source
from commerce_platform.web.retailers import detect_retailer_and_asin

logger = logging.getLogger(__name__)


def _pre_filter(item: ListingItem, min_discount_pct: float) -> bool:
    """Check if item meets minimum discount threshold."""
    if item.discount_pct is not None:
        return item.discount_pct >= min_discount_pct
    if item.price_inr and item.mrp_inr and item.mrp_inr > 0:
        return (item.mrp_inr - item.price_inr) / item.mrp_inr >= min_discount_pct
    return True  # Unknown discount → proceed to PDP


class DealDiscoveryWatcher:
    """Scrapes retailer deal pages, extracts candidates, scores, and stores deals."""

    _LISTING_EXTRACTORS = {
        "amazon_deals": extract_amazon_deal_items,
        "flipkart_deals": extract_flipkart_offer_items,
        "ajio_deals": extract_ajio_offer_items,
        "myntra_deals": extract_myntra_offer_items,
        # Legacy SERP sources — convert to ListingItem wrappers
        "amazon_serp": lambda html, max_items: [
            ListingItem(url=u) for u in extract_amazon_serp_urls(html, max_links=max_items)
        ],
        "flipkart_serp": lambda html, max_items: [
            ListingItem(url=u) for u in extract_flipkart_serp_urls(html, max_links=max_items)
        ],
        "ajio_serp": lambda html, max_items: [
            ListingItem(url=u) for u in extract_ajio_serp_urls(html, max_links=max_items)
        ],
    }

    _DEFAULT_SEED_URLS = {
        "amazon_deals": ["https://www.amazon.in/deals", "https://www.amazon.in/gp/goldbox"],
        "flipkart_deals": ["https://www.flipkart.com/offers/deals-today"],
        "ajio_deals": ["https://www.ajio.com/s/sale"],
        "myntra_deals": ["https://www.myntra.com/offers"],
    }

    def __init__(
        self,
        source: PlatformSourceConfig,
        fetcher: HtmlFetcher,
        catalog_repo: CatalogRepo,
        deal_repo: DealRepo,
        deal_scorer: DealScorer,
        bus: EventBus,
    ) -> None:
        self._source = source
        self._fetcher = fetcher
        self._catalog_repo = catalog_repo
        self._deal_repo = deal_repo
        self._deal_scorer = deal_scorer
        self._bus = bus

    async def run(self) -> None:
        """Main loop: poll deal pages, discover, score, and store deals."""
        seed_urls = [u for u in (self._source.seed_urls or []) if u.strip()]
        if not seed_urls:
            seed_urls = self._DEFAULT_SEED_URLS.get(self._source.type, [])

        if not seed_urls:
            logger.warning(
                "Deal source %s has no seed URLs configured and no defaults available",
                self._source.type,
            )
            return

        logger.info(
            "DealDiscoveryWatcher started: type=%s seeds=%d poll=%ds",
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
                logger.exception("Deal discovery poll error type=%s", self._source.type)
                await asyncio.sleep(min(backoff * 2, 300))
                backoff = min(backoff * 2, 300)
                continue

            await asyncio.sleep(self._source.poll_seconds)

    async def _poll_seed(self, seed_url: str) -> None:
        """Fetch and process a single deal page seed."""
        html = await self._fetcher.get_html(seed_url, label=f"{self._source.type}:listing")
        if html is None:
            logger.warning("Failed to fetch %s seed %s", self._source.type, seed_url)
            return

        extractor = self._LISTING_EXTRACTORS.get(self._source.type)
        if not extractor:
            logger.warning("No extractor for source type %s", self._source.type)
            return

        try:
            items = extractor(html, max_items=self._source.max_links_per_seed)
        except Exception:
            logger.exception("Failed to extract items from %s", seed_url)
            return

        min_disc = self._source.minimum_discount_pct or 0.0
        qualifying = [item for item in items if _pre_filter(item, min_disc)]

        logger.debug(
            "%s: extracted %d items, %d passed pre-filter (min_discount=%.0f%%)",
            self._source.type,
            len(items),
            len(qualifying),
            min_disc * 100,
        )

        for item in qualifying:
            try:
                await self._process_item(item)
            except Exception:
                logger.exception("Failed to process item %s", item.url)
                continue

    async def _process_item(self, item: ListingItem) -> None:
        """Process a single deal candidate: detect retailer, fetch PDP, score, store."""
        retailer, sku = detect_retailer_and_asin(item.url)
        if not retailer:
            logger.debug("Could not detect retailer from URL %s", item.url)
            return

        # Look up product in catalog
        product_id = None
        if sku:
            product_id = await self._catalog_repo.get_product_id_by_retailer_sku(retailer, sku)
        if not product_id:
            product_id = await self._catalog_repo.get_product_id_by_watch_url(item.url)

        # Decide: fetch PDP only if catalog product or listing has no price
        need_pdp = product_id is not None or item.price_inr is None

        price_inr = item.price_inr
        mrp_inr = item.mrp_inr
        in_stock = True
        title = item.title
        image_url = item.image_url

        if need_pdp:
            html = await self._fetcher.get_html(
                item.url,
                label=f"{self._source.type}:{product_id or retailer}",
            )
            if html is None:
                logger.debug("Failed to fetch PDP %s", item.url)
                return

            try:
                parser = get_parser_for_source(retailer)
                signal = parser(html, item.url)
                price_inr = signal.price_inr or item.price_inr
                mrp_inr = signal.mrp_inr or item.mrp_inr
                in_stock = signal.in_stock
                title = signal.listing_title or item.title
                image_url = signal.listing_image_url or item.image_url
            except Exception:
                logger.exception("Failed to parse PDP %s for %s", item.url, retailer)
                return

        # Validate we have at least a price
        if not price_inr:
            logger.debug("No price extracted from %s", item.url)
            return

        if not in_stock:
            logger.debug("%s is out of stock", item.url)
            return

        # Score the deal
        try:
            deal_score = await self._deal_scorer.score_listing(
                product_id=product_id,
                retailer=retailer,
                price_paise=int(price_inr * 100),
                mrp_paise=int(mrp_inr * 100) if mrp_inr else None,
            )
        except Exception:
            logger.exception("Failed to score deal %s", item.url)
            return

        # Upsert into deals table
        from commerce_platform.platform.store.repos.deal_repo import DealRow

        row = DealRow(
            id=None,
            product_url=item.url,
            product_id=product_id,
            retailer=retailer,
            price_paise=int(price_inr * 100),
            mrp_paise=int(mrp_inr * 100) if mrp_inr else None,
            discount_pct=deal_score.discount_pct,
            score=deal_score.score,
            score_reasons=deal_score.reasons,
            product_title=title,
            image_url=image_url,
            source=f"scraper:{self._source.type}",
            is_active=True,
            last_notified_at=None,
            first_seen_at=datetime.now(timezone.utc).isoformat(),
            last_confirmed_at=datetime.now(timezone.utc).isoformat(),
        )

        try:
            action, should_notify = await self._deal_repo.upsert(row)
            logger.debug(
                "Deal %s: action=%s notify=%s score=%.2f",
                item.url,
                action,
                should_notify,
                deal_score.score,
            )
        except Exception:
            logger.exception("Failed to upsert deal %s", item.url)
            return

        # Publish PriceObservation for catalog products (keeps price history fresh, triggers alerts)
        if product_id:
            try:
                obs = PriceObservation(
                    product_id=product_id,
                    retailer=retailer,
                    price_paise=int(price_inr * 100),
                    mrp_paise=int(mrp_inr * 100) if mrp_inr else None,
                    in_stock=in_stock,
                    source=f"scraper:{self._source.type}",
                    observed_at=datetime.now(timezone.utc).isoformat(),
                    product_url=item.url,
                    product_title=title,
                    context={
                        "deal_score": deal_score.score,
                        "deal_action": action,
                        "deal_reasons": deal_score.reasons,
                    },
                )
                await self._bus.publish(obs)
            except Exception:
                logger.exception("Failed to publish observation for %s", product_id)
