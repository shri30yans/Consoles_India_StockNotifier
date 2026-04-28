from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import AsyncIterator, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")
logger = logging.getLogger(__name__)


@runtime_checkable
class EventBus(Protocol):
    async def publish(self, topic: str, event: object) -> None: ...
    def subscribe(self, topic: str, *, maxsize: int = 1024) -> AsyncIterator[object]: ...


class _Subscription(Generic[T]):
    def __init__(self, queue: asyncio.Queue[T]) -> None:
        self._queue = queue

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        return await self._queue.get()


class InMemoryBus:
    """Single-process pub/sub. Good for v1 and tests; replaceable.

    Each subscriber gets its own bounded queue. Slow subscribers do NOT
    block publishers — overflows are dropped with a WARN log (back-pressure
    is a deployment concern, not a domain concern).
    """

    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)

    async def publish(self, topic: str, event: object) -> None:
        for q in list(self._subs.get(topic, ())):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Bus topic %r dropped event (subscriber slow)", topic)

    def subscribe(self, topic: str, *, maxsize: int = 1024) -> _Subscription:
        q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._subs[topic].append(q)
        return _Subscription(q)


# Canonical topic names — keep in one place to avoid typos.
class Topics:
    CANDIDATE = "deal.candidate"
    ENRICHED = "deal.enriched"
    SCORED = "deal.scored"
    PUBLISHABLE = "deal.publishable"
