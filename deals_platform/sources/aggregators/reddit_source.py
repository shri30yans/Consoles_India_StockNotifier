"""Reddit aggregator — polls subreddits like r/IndiaDeals, r/bapcsalesindia.

Uses asyncpraw with read-only credentials. Each post that links to a
recognized retailer becomes a DealCandidate.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import AsyncIterator

from deals_platform.domain.events import DealCandidate

logger = logging.getLogger(__name__)

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


class RedditSource:
    name = "aggregator:reddit"

    def __init__(
        self,
        subreddits: list[str],
        *,
        poll_seconds: int = 300,
    ) -> None:
        self._subs = subreddits
        self._poll = poll_seconds
        self._queue: asyncio.Queue[DealCandidate] = asyncio.Queue(maxsize=2048)
        self._seen: set[str] = set()

    async def stream(self) -> AsyncIterator[DealCandidate]:
        loop = asyncio.create_task(self._poll_loop(), name="reddit-poll")
        try:
            while True:
                yield await self._queue.get()
        finally:
            loop.cancel()
            await asyncio.gather(loop, return_exceptions=True)

    async def _poll_loop(self) -> None:
        try:
            import asyncpraw  # local import: optional dep
        except ImportError:
            logger.warning("asyncpraw not installed; RedditSource disabled")
            return

        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        ua = os.environ.get("REDDIT_USER_AGENT", "DealsPlatform/0.1")
        if not (client_id and client_secret):
            logger.warning("REDDIT_CLIENT_ID/SECRET missing; RedditSource disabled")
            return

        reddit = asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=ua,
        )
        try:
            while True:
                for name in self._subs:
                    try:
                        sub = await reddit.subreddit(name)
                        async for post in sub.new(limit=25):
                            if post.id in self._seen:
                                continue
                            self._seen.add(post.id)
                            url = getattr(post, "url", None)
                            if not url:
                                continue
                            retailer = _retailer_for(url)
                            if retailer is None:
                                continue
                            await self._queue.put(
                                DealCandidate(
                                    source=self.name,
                                    retailer=retailer,
                                    product_url=_strip_tracking(url),
                                    title=getattr(post, "title", None),
                                    raw_payload={
                                        "reddit_id": post.id,
                                        "subreddit": name,
                                        "score": getattr(post, "score", 0),
                                    },
                                )
                            )
                    except Exception:
                        logger.exception("reddit poll failed for r/%s", name)
                await asyncio.sleep(self._poll)
        finally:
            await reddit.close()


def _strip_tracking(url: str) -> str:
    return re.sub(r"([?&])(?:tag|aff_id|affid|utm_[^=&]+|ref|smid)=[^&]*", r"\1", url).rstrip("?&")
