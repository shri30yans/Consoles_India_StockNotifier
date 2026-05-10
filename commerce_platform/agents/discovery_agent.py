"""AI-native deal discovery agent — autonomous deal finding with adaptive parser fixing."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from commerce_platform.platform.store.repos import CatalogRepo, DealRepo, ConfigSettingsRepo, PriceRepo
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.events.observation import PriceObservation
from commerce_platform.stock.sources.serp_parsers import ListingItem
from commerce_platform.deals.scorer import DealScorer, DealScore

logger = logging.getLogger(__name__)

tz = timezone.utc


@dataclass
class DiscoveryResult:
    """Result of a discovery pass."""
    source_type: str
    seed_url: str
    items_found: int
    items_qualified: int
    deals_created: int
    deals_updated: int
    errors: list[str]
    parser_suggestion: str | None = None


class DealDiscoveryAgent:
    """Autonomous agent that discovers deals from retailer pages.

    Flow:
    1. Fetch retailer deal page
    2. Parse with listed extractor (if fails, suggest fix)
    3. Pre-filter by minimum_discount_pct
    4. Fetch PDP for unknowns
    5. Score vs 90d history
    6. Upsert to deals table
    7. Publish PriceObservation for catalog products
    """

    def __init__(
        self,
        source_type: str,
        seed_urls: list[str],
        minimum_discount_pct: float,
        fetcher,
        catalog_repo: CatalogRepo,
        deal_repo: DealRepo,
        deal_scorer: DealScorer,
        bus: EventBus,
        config_repo: ConfigSettingsRepo,
    ):
        self.source_type = source_type
        self.seed_urls = seed_urls
        self.minimum_discount_pct = minimum_discount_pct
        self._fetcher = fetcher
        self._catalog_repo = catalog_repo
        self._deal_repo = deal_repo
        self._deal_scorer = deal_scorer
        self._bus = bus
        self._config_repo = config_repo

    async def discover(self) -> DiscoveryResult:
        """Execute one discovery pass. Returns result with metrics and any parser suggestions."""
        results = []
        for seed_url in self.seed_urls:
            r = await self._discover_from_seed(seed_url)
            results.append(r)

        # Aggregate
        total_found = sum(r.items_found for r in results)
        total_qualified = sum(r.items_qualified for r in results)
        total_created = sum(r.deals_created for r in results)
        total_updated = sum(r.deals_updated for r in results)
        all_errors = [e for r in results for e in r.errors]
        parser_suggestions = [r.parser_suggestion for r in results if r.parser_suggestion]

        return DiscoveryResult(
            source_type=self.source_type,
            seed_url=" + ".join(self.seed_urls),
            items_found=total_found,
            items_qualified=total_qualified,
            deals_created=total_created,
            deals_updated=total_updated,
            errors=all_errors,
            parser_suggestion=parser_suggestions[0] if parser_suggestions else None,
        )

    async def _discover_from_seed(self, seed_url: str) -> DiscoveryResult:
        """Discover deals from a single seed URL."""
        result = DiscoveryResult(
            source_type=self.source_type,
            seed_url=seed_url,
            items_found=0,
            items_qualified=0,
            deals_created=0,
            deals_updated=0,
            errors=[],
        )

        try:
            html = await self._fetcher.get_html(seed_url, label=f"{self.source_type}:listing")
            if not html:
                result.errors.append(f"Failed to fetch {seed_url}")
                return result

            # Get extractor for this source type
            from commerce_platform.stock.sources.serp_parsers import (
                extract_amazon_deal_items,
                extract_flipkart_offer_items,
                extract_ajio_offer_items,
                extract_myntra_offer_items,
            )

            extractors = {
                "amazon_deals": extract_amazon_deal_items,
                "flipkart_deals": extract_flipkart_offer_items,
                "ajio_deals": extract_ajio_offer_items,
                "myntra_deals": extract_myntra_offer_items,
            }

            extractor = extractors.get(self.source_type)
            if not extractor:
                result.errors.append(f"No extractor for {self.source_type}")
                return result

            # Try to extract items
            try:
                items = extractor(html, max_items=100)
                result.items_found = len(items)
            except ValueError as e:
                # Parser failed — suggest fix via LLM
                result.errors.append(f"Parser failed: {e}")
                result.parser_suggestion = await self._suggest_parser_fix(html, str(e))
                return result

            # Pre-filter by discount
            qualified = [i for i in items if self._passes_prefilter(i)]
            result.items_qualified = len(qualified)

            logger.info(f"{self.source_type}: {len(qualified)}/{result.items_found} items passed pre-filter")

            # Process each qualified item
            for item in qualified:
                try:
                    await self._process_item(item, result)
                except Exception as e:
                    logger.exception(f"Error processing {item.url}: {e}")
                    result.errors.append(f"Item processing failed: {str(e)}")

        except Exception as e:
            logger.exception(f"Discovery from {seed_url} failed: {e}")
            result.errors.append(f"Discovery failed: {str(e)}")

        return result

    def _passes_prefilter(self, item: ListingItem) -> bool:
        """Check if item meets minimum discount threshold."""
        if item.discount_pct is not None:
            return item.discount_pct >= self.minimum_discount_pct

        if item.price_inr and item.mrp_inr and item.mrp_inr > 0:
            calculated_discount = (item.mrp_inr - item.price_inr) / item.mrp_inr
            return calculated_discount >= self.minimum_discount_pct

        return True  # Unknown discount — proceed to scoring

    async def _process_item(self, item: ListingItem, result: DiscoveryResult) -> None:
        """Process a single listing item → fetch PDP if needed → score → upsert."""
        from commerce_platform.stock.parsers.protocol import get_parser_for_source
        from commerce_platform.web.listing_scrape import detect_retailer_and_asin

        retailer, sku = detect_retailer_and_asin(item.url)
        if not retailer:
            return

        # Look up product in catalog
        product_id = (
            await self._catalog_repo.get_product_id_by_retailer_sku(retailer, sku)
            or await self._catalog_repo.get_product_id_by_watch_url(item.url)
        )

        # Fetch PDP if needed
        price_inr = item.price_inr
        mrp_inr = item.mrp_inr
        in_stock = True
        title = item.title
        image = item.image_url

        if product_id or item.price_inr is None:
            html = await self._fetcher.get_html(item.url, label=f"{self.source_type}:{product_id or retailer}")
            if html:
                try:
                    parser = get_parser_for_source(retailer)
                    signal = parser(html, item.url)
                    price_inr = signal.price_inr or item.price_inr
                    mrp_inr = signal.mrp_inr or item.mrp_inr
                    in_stock = signal.in_stock
                    title = signal.listing_title or item.title
                    image = signal.listing_image_url or item.image_url
                except Exception as e:
                    logger.warning(f"PDP parse failed for {item.url}: {e}")
                    if not item.price_inr:
                        return  # No price from listing either

        if not price_inr or not in_stock:
            return

        # Score the deal
        deal_score = await self._deal_scorer.score_listing(
            product_id=product_id,
            retailer=retailer,
            price_paise=int(price_inr * 100),
            mrp_paise=int(mrp_inr * 100) if mrp_inr else None,
        )

        # Upsert into deals table
        from commerce_platform.platform.store.repos.deal_repo import DealRow

        action, should_notify = await self._deal_repo.upsert(
            DealRow(
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
                image_url=image,
                source=f"scraper:{self.source_type}",
                is_active=True,
                last_notified_at=None,
                first_seen_at=datetime.now(tz).isoformat(),
                last_confirmed_at=datetime.now(tz).isoformat(),
            )
        )

        if action == "inserted":
            result.deals_created += 1
        elif action in ("price_improved", "reactivated"):
            result.deals_updated += 1

        # Publish PriceObservation for catalog products (triggers existing rule engine)
        if product_id:
            await self._bus.publish(
                PriceObservation(
                    product_id=product_id,
                    retailer=retailer,
                    price_paise=int(price_inr * 100),
                    mrp_paise=int(mrp_inr * 100) if mrp_inr else None,
                    in_stock=in_stock,
                    source=f"scraper:{self.source_type}",
                    observed_at=datetime.now(tz).isoformat(),
                    product_url=item.url,
                    product_title=title,
                    context={"deal_score": deal_score.score, "action": action},
                )
            )

    async def _suggest_parser_fix(self, html: str, error: str) -> str:
        """Use LLM to analyze HTML and suggest selector fixes."""
        # This is where you'd call Claude API to analyze the page structure
        # and suggest updated CSS selectors. For now, return structured error.
        suggestion = (
            f"Parser error: {error}\n\n"
            f"Recommendation: Use Playwright to inspect page structure:\n"
            f"  1. await page.goto(url)\n"
            f"  2. await page.pause()  # Opens inspector\n"
            f"  3. Inspect product cards, note new class names\n"
            f"  4. Update regex patterns in serp_parsers.py\n"
            f"  5. Re-run test to verify\n"
            f"\nHTML length: {len(html)} bytes"
        )
        return suggestion
