"""Discord notifier — posts to a webhook URL."""

from __future__ import annotations

import logging
import os

from commerce_platform.platform.notify._http_channel import BaseHttpChannel, ChannelError
from commerce_platform.platform.notify.retry import with_retries

logger = logging.getLogger(__name__)


class DiscordNotifier(BaseHttpChannel):
    def __init__(self, *, retries: int = 4) -> None:
        self._retries = retries

    async def send(self, text: str, webhook_url: str) -> None:
        resolved = (
            webhook_url
            if webhook_url.startswith("http")
            else os.environ.get(webhook_url, webhook_url)
        )

        async def _send() -> None:
            try:
                await self._post_json(resolved, {"content": text})
            except ChannelError as e:
                raise RuntimeError(
                    f"Discord webhook {e.status}: {(e.body_preview or '')[:200]}",
                ) from e

        await with_retries(_send, retries=self._retries, label="discord")
