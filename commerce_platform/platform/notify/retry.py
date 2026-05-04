"""Shared exponential backoff retry for notification sends."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def with_retries(
    fn: Callable[[], Awaitable[T]],
    *,
    retries: int = 4,
    backoff_base: float = 1.5,
    label: str = "",
) -> T | None:
    for attempt in range(retries):
        try:
            return await fn()
        except asyncio.TimeoutError:
            logger.warning("%s timeout attempt %d/%d", label, attempt + 1, retries)
        except Exception as e:
            logger.warning("%s error attempt %d/%d: %s", label, attempt + 1, retries, e)
        if attempt < retries - 1:
            await asyncio.sleep(backoff_base**attempt)
    logger.error("%s failed after %d retries", label, retries)
    return None
