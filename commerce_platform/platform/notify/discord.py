"""Discord notifier — posts to a webhook URL."""

from __future__ import annotations

import logging
import os

import aiohttp

from commerce_platform.platform.notify.retry import with_retries

logger = logging.getLogger(__name__)


class DiscordNotifier:
    def __init__(self, *, retries: int = 4) -> None:
        self._retries = retries

    async def send(self, text: str, webhook_url: str) -> None:
        resolved = os.environ.get(webhook_url, webhook_url) if not webhook_url.startswith("http") else webhook_url

        async def _send() -> None:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    resolved,
                    json={"content": text},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status >= 400:
                        body = await resp.text()
                        raise RuntimeError(f"Discord webhook {resp.status}: {body[:200]}")

        await with_retries(_send, retries=self._retries, label="discord")
