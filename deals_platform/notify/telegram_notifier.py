from __future__ import annotations

import asyncio
import logging
import os

import aiohttp

from deals_platform.domain.events import PublishablePost
from deals_platform.notify.formatting import render_telegram_markdown

logger = logging.getLogger(__name__)


class TelegramNotifier:
    name = "telegram"

    def __init__(self, *, retries: int = 4, backoff_base: float = 1.5) -> None:
        self._token = os.environ.get("TELEGRAM_TOKEN")
        self._retries = retries
        self._backoff = backoff_base

    async def send(self, post: PublishablePost, channel_target: str) -> None:
        if not self._token:
            logger.warning("TELEGRAM_TOKEN missing; skipping send")
            return
        chat_id = os.environ.get(channel_target) or channel_target
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": render_telegram_markdown(post),
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        for attempt in range(self._retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status < 400:
                            return
                        body = await resp.text()
                        logger.warning(
                            "telegram %s attempt %d: %s", resp.status, attempt + 1, body[:200]
                        )
            except asyncio.TimeoutError:
                logger.warning("telegram timeout attempt %d", attempt + 1)
            if attempt < self._retries - 1:
                await asyncio.sleep(self._backoff**attempt)
        logger.error("telegram send failed after retries")
