"""DesiDime aggregator source.

We poll the public 'hot deals' RSS-like listing, extract retailer URLs from
each deal page, and emit DealCandidates. Re-verification (current price/stock)
happens downstream in the Normalizer — never trust aggregator copy verbatim.

Note: respect their ToS — modest poll interval, identifying UA. This source
is OPT-IN via config and disabled by default.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import AsyncIterator

from bs4 import BeautifulSoup

from deals_platform.domain.events import DealCandidate
from stock_notifier.fetch import HtmlFetcher

logger = logging.getLogger(__name__)

_DEFAULT_LIST_URL = "https://www.desidime.com/deals/hot-online-deals"

_RETAILER_HOSTS = {
    "amazon.in": "amazon",
    "amzn.to": "amazon",
    "flipkart.com": "flipkart",
    "fkrt.it": "flipkart",
    "croma.com": "croma",
    "myntra.com": "myntra",
    "ajio.com": "ajio",
    "tatacliq.com": "tatacliq",
    "reliancedigital.in": "reliance_digital",
}


def _retailer_for(url: str) -> str | None:
    for host, key in _RETAILER_HOSTS.items():
        if host in url:
            return key
    return None


class DesiDimeSource:
    name = "aggregator:desidime"

    def __init__(
        self,
        fetcher: HtmlFetcher,
        *,
        list_url: str = _DEFAULT_LIST_URL,
        poll_seconds: int = 900,
    ) -> None:
        self._fetcher = fetcher
        self._list_url = list_url
        self._poll = poll_seconds
        self._seen: set[str] = set()
        self._queue: asyncio.Queue[DealCandidate] = asyncio.Queue(maxsize=2048)

    async def stream(self) -> AsyncIterator[DealCandidate]:
        loop = asyncio.create_task(self._poll_loop(), name="desidime-poll")
        try:
            while True:
                yield await self._queue.get()
        finally:
            loop.cancel()
            await asyncio.gather(loop, return_exceptions=True)

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self._poll_once()
            except Exception:
                logger.exception("desidime poll failed")
            await asyncio.sleep(self._poll)

    async def _poll_once(self) -> None:
        html = await self._fetcher.get_html(
            self._list_url, None, product_key="(desidime)", website_key="desidime"
        )
        if not html:
            return
        soup = BeautifulSoup(html, "lxml")
        # Each deal card links to a /deals/<slug> page; we then need to follow to
        # find the outbound retailer URL. Selectors are best-effort and may need
        # tuning over time; failing softly is the right behavior.
        for a in soup.select("a[href^='/deals/']"):
            href = a.get("href")
            if not href or href in self._seen:
                continue
            self._seen.add(href)
            asyncio.create_task(self._resolve_outbound(f"https://www.desidime.com{href}"))

    async def _resolve_outbound(self, deal_page: str) -> None:
        try:
            html = await self._fetcher.get_html(
                deal_page, None, product_key="(desidime)", website_key="desidime"
            )
            if not html:
                return
            # The outbound URL on DesiDime is usually an <a> with rel="nofollow"
            # pointing to the retailer.
            soup = BeautifulSoup(html, "lxml")
            outbound = None
            for a in soup.find_all("a", href=True):
                href = a["href"]
                retailer = _retailer_for(href)
                if retailer is not None:
                    outbound = (retailer, href)
                    break
            if outbound is None:
                return
            retailer, url = outbound
            title_el = soup.select_one("h1, .deal-title")
            title = title_el.get_text(strip=True) if title_el else None
            await self._queue.put(
                DealCandidate(
                    source=self.name,
                    retailer=retailer,
                    product_url=_strip_tracking(url),
                    title=title,
                    raw_payload={"deal_page": deal_page},
                )
            )
        except Exception:
            logger.exception("desidime resolve failed for %s", deal_page)


def _strip_tracking(url: str) -> str:
    """Remove other people's affiliate/tracking params; we'll add ours later."""
    # Strip aff_id/affid/tag/utm_*/ref params, keep core ASIN/itm path.
    return re.sub(r"([?&])(?:tag|aff_id|affid|utm_[^=&]+|ref|smid)=[^&]*", r"\1", url).rstrip("?&")
