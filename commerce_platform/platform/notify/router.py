"""Channel router — maps channel ID → list of (notifier, target) pairs."""

from __future__ import annotations

import asyncio
import logging
import os

from commerce_platform.platform.config.schema import ChannelConfig
from commerce_platform.platform.notify.discord import DiscordNotifier
from commerce_platform.platform.notify.telegram import TelegramNotifier

logger = logging.getLogger(__name__)


class ChannelRouter:
    def __init__(self, channels: list[ChannelConfig]) -> None:
        self._telegram = TelegramNotifier()
        self._discord = DiscordNotifier()
        self._channels = {c.id: c for c in channels}

    async def send(self, channel_id: str, text: str) -> None:
        channel = self._channels.get(channel_id)
        if channel is None:
            logger.warning("Unknown channel: %s", channel_id)
            return

        tasks = []
        if channel.telegram:
            chat_id = _resolve(channel.telegram.chat_id)
            if chat_id:
                tasks.append(self._telegram.send(text, chat_id))
        if channel.discord:
            webhook = _resolve(channel.discord.webhook_url)
            if webhook:
                tasks.append(self._discord.send(text, webhook))

        if not tasks:
            logger.warning("Channel %s has no configured notifiers", channel_id)
            return

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.error("Channel %s send failed: %s", channel_id, r)

    async def fan_out(self, channel_ids: list[str], text: str) -> None:
        await asyncio.gather(
            *(self.send(cid, text) for cid in channel_ids),
            return_exceptions=True,
        )

    def get_telegram(self) -> TelegramNotifier:
        return self._telegram


def _resolve(value: str) -> str:
    if value.startswith("env:"):
        var = value[4:]
        return os.environ.get(var, "")
    return value
