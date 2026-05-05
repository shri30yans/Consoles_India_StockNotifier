"""WishlistWatcher — polls an Amazon wishlist; emits price observations."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from commerce_platform.platform.config.schema import PlatformSourceConfig
from commerce_platform.platform.config.wishlist_key import resolve_wishlist_list_key
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.events.observation import PriceObservation
from commerce_platform.platform.fetch.protocol import HtmlFetcher
from commerce_platform.platform.store.repos import CatalogRepo
from commerce_platform.stock.parsers.amazon import parse_wishlist

logger = logging.getLogger(__name__)


class WishlistWatcher:
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
        self._list_key = resolve_wishlist_list_key(source)

    async def run(self) -> None:
        url = self._source.url
        if not url:
            logger.error("amazon_wishlist source has no url configured")
            return

        logger.info(
            "Wishlist watcher started: list_key=%s url=%s interval=%ds channels=%s",
            self._list_key,
            url,
            self._source.poll_seconds,
            self._source.channels or "(none — no alert rules for this list)",
        )
        backoff = 1.0
        cycle = 0
        while True:
            cycle += 1
            try:
                await self._poll(url, cycle)
                backoff = 1.0
            except Exception:
                logger.exception("Wishlist poll error (cycle %d): %s", cycle, url)
                await asyncio.sleep(min(backoff * 2, 300))
                backoff = min(backoff * 2, 300)
                continue
            logger.debug(
                "Wishlist cycle %d: sleeping %ds before next scrape",
                cycle,
                self._source.poll_seconds,
            )
            await asyncio.sleep(self._source.poll_seconds)

    async def _poll(self, url: str, cycle: int) -> None:
        logger.debug("Wishlist cycle %d: fetching wishlist HTML…", cycle)
        page_html = await self._fetcher.get_html(url, label="wishlist")
        if page_html is None:
            logger.warning(
                "Wishlist cycle %d: no HTML returned (blocked, captcha, or fetch error?) url=%s",
                cycle,
                url,
            )
            return

        logger.debug(
            "Wishlist cycle %d: fetched OK — %d byte(s) HTML",
            cycle,
            len(page_html),
        )

        items = parse_wishlist(page_html)
        if not items:
            logger.warning(
                "Wishlist cycle %d: parser returned 0 items — login required, empty list, or Amazon layout changed. url=%s",
                cycle,
                url,
            )
            return

        logger.debug("Wishlist cycle %d: parsed %d item(s)", cycle, len(items))
        for idx, item in enumerate(items, start=1):
            price_txt = f"₹{item.price_inr:,.0f}" if item.price_inr else "—"
            stock_txt = "IN_STOCK" if item.in_stock else "OUT_OF_STOCK"
            logger.debug(
                "Wishlist cycle %d: item %d/%d asin=%s status=%s price=%s name=%s",
                cycle,
                idx,
                len(items),
                item.asin,
                stock_txt,
                price_txt,
                item.name[:120] + ("…" if len(item.name) > 120 else ""),
            )
            await self._check_item(item, cycle)

        logger.debug(
            "Wishlist cycle %d: scrape complete — processed %d wishlist row(s)",
            cycle,
            len(items),
        )

    async def _check_item(self, item, cycle: int) -> None:
        page_url = f"https://www.amazon.in/dp/{item.asin}/"

        # Try to resolve ASIN to a configured product
        product_id = await self._catalog_repo.get_product_id_by_retailer_sku("amazon", item.asin)

        if product_id is None:
            logger.debug(
                "Wishlist item not in catalog: asin=%s name=%s (skipping — no tracking rules)",
                item.asin,
                item.name,
            )
            return

        # Create observation
        observation = PriceObservation(
            product_id=product_id,
            retailer="amazon_wishlist",  # ← Distinct from "amazon" scraper
            price_paise=int(item.price_inr * 100) if item.price_inr else 0,
            mrp_paise=None,
            in_stock=item.in_stock,
            source=f"wishlist:{self._list_key}",
            observed_at=datetime.now(timezone.utc).isoformat(),
            product_url=page_url,
            product_title=item.name,
        )

        # Emit observation
        await self._bus.publish(observation)
