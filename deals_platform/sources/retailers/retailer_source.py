"""Retailer scraper Source — produces DealCandidate per polled URL.

Reuses `stock_notifier.fetch` for HTTP/Playwright and a price-extracting
parser shim. We do NOT modify any existing module.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import AsyncIterator

from deals_platform.domain.events import DealCandidate
from deals_platform.domain.models import Money
from deals_platform.sources.retailers.price_extract import extract_price_signal
from deals_platform.sources.spec import WatchSpec
from stock_notifier.fetch import HtmlFetcher

logger = logging.getLogger(__name__)


class RetailerWatchSource:
    """Polls a list of WatchSpecs concurrently, emits DealCandidates."""

    def __init__(
        self,
        name: str,
        watches: list[WatchSpec],
        fetcher: HtmlFetcher,
        *,
        jitter_max: float = 5.0,
    ) -> None:
        self.name = name
        self._watches = watches
        self._fetcher = fetcher
        self._jitter = jitter_max
        self._queue: asyncio.Queue[DealCandidate] = asyncio.Queue(maxsize=1024)

    async def stream(self) -> AsyncIterator[DealCandidate]:
        workers = [
            asyncio.create_task(self._poll_loop(w), name=f"watch:{w.retailer}:{w.url[-30:]}")
            for w in self._watches
        ]
        try:
            while True:
                yield await self._queue.get()
        finally:
            for t in workers:
                t.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

    async def _poll_loop(self, watch: WatchSpec) -> None:
        # Stagger startup to avoid stampede.
        await asyncio.sleep(random.uniform(0, self._jitter))
        while True:
            try:
                await self._poll_once(watch)
            except Exception:
                logger.exception("poll failed for %s %s", watch.retailer, watch.url)
            await asyncio.sleep(watch.poll_seconds + random.uniform(0, self._jitter))

    async def _poll_once(self, watch: WatchSpec) -> None:
        html = await self._fetcher.get_html(
            watch.url,
            None,
            product_key="(deals)",
            website_key=watch.retailer,
        )
        if not html:
            return
        parsed = extract_price_signal(html, watch.retailer, watch.url)
        if parsed is None:
            return
        title, price_rupees, mrp_rupees = parsed
        candidate = DealCandidate(
            source=f"scraper:{watch.retailer}",
            retailer=watch.retailer,
            product_url=watch.url,
            title=title or watch.title_hint,
            observed_price=Money.from_rupees(price_rupees) if price_rupees else None,
            observed_mrp=Money.from_rupees(mrp_rupees) if mrp_rupees else None,
        )
        await self._queue.put(candidate)
