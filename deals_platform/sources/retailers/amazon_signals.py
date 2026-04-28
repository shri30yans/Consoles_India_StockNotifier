"""Amazon-first source signals.

Discovers product links from configurable Amazon seed pages (e.g. deals pages),
then verifies each product page to extract price/MRP before emitting candidates.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import AsyncIterator
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from deals_platform.domain.events import DealCandidate
from deals_platform.domain.models import Money
from deals_platform.sources.retailers.price_extract import extract_price_signal
from stock_notifier.fetch import HtmlFetcher

logger = logging.getLogger(__name__)

_ASIN_RE = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?]|$)")


def _canonical_amazon_product_url(url: str) -> str | None:
    match = _ASIN_RE.search(url)
    if not match:
        return None
    asin = match.group(1)
    return f"https://www.amazon.in/dp/{asin}"


def _normalize_amazon_url(base_url: str, href: str) -> str | None:
    joined = urljoin(base_url, href)
    parsed = urlparse(joined)
    if "amazon.in" not in parsed.netloc:
        return None
    # Drop query/fragment to reduce duplicates.
    stripped = parsed._replace(query="", fragment="")
    canon = _canonical_amazon_product_url(urlunparse(stripped))
    return canon


class AmazonSignalsSource:
    """Continuously discovers Amazon product candidates from seed pages."""

    name = "scraper:amazon:signals"

    def __init__(
        self,
        fetcher: HtmlFetcher,
        *,
        seed_urls: list[str],
        poll_seconds: int = 900,
        max_links_per_seed: int = 20,
        jitter_max: float = 5.0,
    ) -> None:
        self._fetcher = fetcher
        self._seed_urls = seed_urls
        self._poll_seconds = poll_seconds
        self._max_links = max_links_per_seed
        self._jitter = jitter_max
        self._queue: asyncio.Queue[DealCandidate] = asyncio.Queue(maxsize=2048)
        self._seen_urls: set[str] = set()

    async def stream(self) -> AsyncIterator[DealCandidate]:
        worker = asyncio.create_task(self._loop(), name="amazon-signals")
        try:
            while True:
                yield await self._queue.get()
        finally:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)

    async def _loop(self) -> None:
        await asyncio.sleep(random.uniform(0, self._jitter))
        while True:
            for seed in self._seed_urls:
                try:
                    await self._poll_seed(seed)
                except Exception:
                    logger.exception("amazon seed polling failed: %s", seed)
            await asyncio.sleep(self._poll_seconds + random.uniform(0, self._jitter))

    async def _poll_seed(self, seed_url: str) -> None:
        html = await self._fetcher.get_html(
            seed_url,
            None,
            product_key="(amazon-signals)",
            website_key="amazon",
        )
        if not html:
            return

        soup = BeautifulSoup(html, "lxml")
        discovered: list[str] = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            normalized = _normalize_amazon_url(seed_url, href)
            if not normalized:
                continue
            if normalized in self._seen_urls:
                continue
            self._seen_urls.add(normalized)
            discovered.append(normalized)
            if len(discovered) >= self._max_links:
                break

        for product_url in discovered:
            await self._emit_from_product_url(product_url)

    async def _emit_from_product_url(self, product_url: str) -> None:
        html = await self._fetcher.get_html(
            product_url,
            None,
            product_key="(amazon-signals)",
            website_key="amazon",
        )
        if not html:
            return
        parsed = extract_price_signal(html, "amazon", product_url)
        if parsed is None:
            return
        title, price_rupees, mrp_rupees = parsed
        if price_rupees is None:
            return
        await self._queue.put(
            DealCandidate(
                source=self.name,
                retailer="amazon",
                product_url=product_url,
                title=title,
                observed_price=Money.from_rupees(price_rupees),
                observed_mrp=Money.from_rupees(mrp_rupees) if mrp_rupees else None,
                raw_payload={"seed_discovery": True},
            )
        )
