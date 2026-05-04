"""Typed async in-memory event bus.

Each subscriber gets its own bounded asyncio.Queue. Publish is non-blocking
(drops oldest event if queue full — prevents slow consumers from blocking producers).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EventBus:
    def __init__(self, queue_size: int = 2048) -> None:
        self._queue_size = queue_size
        self._subscribers: dict[type, list[asyncio.Queue]] = {}

    def subscribe(self, event_type: type[T]) -> asyncio.Queue[T]:
        q: asyncio.Queue[T] = asyncio.Queue(maxsize=self._queue_size)
        self._subscribers.setdefault(event_type, []).append(q)
        return q

    async def publish(self, event: object) -> None:
        for q in self._subscribers.get(type(event), []):
            if q.full():
                logger.warning(
                    "EventBus queue full for %s; dropping oldest event",
                    type(event).__name__,
                )
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await q.put(event)

    async def iter_events(self, queue: asyncio.Queue[T]) -> AsyncIterator[T]:
        while True:
            yield await queue.get()
