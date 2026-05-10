from __future__ import annotations

import asyncio
from datetime import datetime

from commerce_platform.deals.bus import InMemoryBus, iter_candidates
from commerce_platform.deals.bus.bus import Topics
from commerce_platform.deals.domain.events import DealCandidate
from commerce_platform.deals.domain.models import Category, Money


def test_iter_candidates_roundtrip() -> None:
    async def body() -> None:
        bus = InMemoryBus()
        cand = DealCandidate(
            source="test",
            retailer="amazon",
            product_url="https://www.amazon.in/dp/B000TEST000",
            category=Category.tech,
            title="Test",
            observed_price=Money.from_rupees(99.0),
            discovered_at=datetime.utcnow(),
        )
        await bus.publish(Topics.CANDIDATE, cand)
        sub = iter_candidates(bus)
        out = await sub.__anext__()
        assert out.product_url == cand.product_url
        assert out.observed_price == cand.observed_price

    asyncio.run(body())
