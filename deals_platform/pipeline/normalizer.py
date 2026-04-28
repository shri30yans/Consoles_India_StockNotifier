"""Normalize a DealCandidate into an EnrichedDeal.

Steps:
  1. Resolve canonical product id
  2. Append current observation to price history
  3. Look up history (90d min, 30d median, cross-retailer min)
  4. Emit EnrichedDeal
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from deals_platform.domain.events import DealCandidate, EnrichedDeal
from deals_platform.domain.models import Money, PriceSnapshot
from deals_platform.domain.ports import (
    CanonicalResolver,
    DedupeStore,
    PriceHistoryRepo,
)

logger = logging.getLogger(__name__)


class Normalizer:
    def __init__(
        self,
        history: PriceHistoryRepo,
        resolver: CanonicalResolver,
        dedupe: DedupeStore,
    ) -> None:
        self._history = history
        self._resolver = resolver
        self._dedupe = dedupe

    async def normalize(self, candidate: DealCandidate) -> EnrichedDeal | None:
        # Idempotency: same URL on the same day = process once.
        if await self._dedupe.seen(candidate.fingerprint()):
            return None
        await self._dedupe.remember(candidate.fingerprint(), ttl_seconds=24 * 3600)

        if candidate.observed_price is None:
            logger.debug("skip candidate without price: %s", candidate.product_url)
            return None

        canonical_id = await self._resolver.resolve(candidate)

        snap = PriceSnapshot(
            product_canonical_id=canonical_id,
            retailer=candidate.retailer,
            price=candidate.observed_price,
            mrp=candidate.observed_mrp,
            in_stock=True,  # if we got a price, assume listed; refine later
            rating=None,
            rating_count=None,
        )
        try:
            await self._history.append(snap)
        except Exception:
            logger.exception("price history append failed")

        now = datetime.utcnow()
        try:
            min_90 = await self._history.min_since(
                canonical_id, candidate.retailer, now - timedelta(days=90)
            )
            median_30 = await self._history.median_since(
                canonical_id, candidate.retailer, now - timedelta(days=30)
            )
            cross_min = await self._history.cross_retailer_min(canonical_id)
        except Exception:
            logger.exception("history lookup failed")
            min_90 = median_30 = cross_min = None

        return EnrichedDeal(
            candidate=candidate,
            canonical_id=canonical_id,
            title=candidate.title or "Unknown product",
            brand=None,
            image_url=None,
            snapshot=snap,
            history_min_90d=min_90,
            history_median_30d=median_30,
            cross_retailer_min=cross_min,
            offers=(),
        )

    @staticmethod
    def _better(a: Money | None, b: Money | None) -> Money | None:
        if a is None:
            return b
        if b is None:
            return a
        return a if a.minor_units <= b.minor_units else b
