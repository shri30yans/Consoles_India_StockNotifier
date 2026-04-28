"""Discord notifier via webhook URL OR bot token + channel id.

Webhook is simpler (no gateway connection); we use that path. The env value
referred to by `channel_target` should be a webhook URL.
"""

from __future__ import annotations

import logging
import os

import aiohttp

from deals_platform.domain.events import PublishablePost
from deals_platform.notify.formatting import render_plain

logger = logging.getLogger(__name__)


class DiscordNotifier:
    name = "discord"

    async def send(self, post: PublishablePost, channel_target: str) -> None:
        webhook = os.environ.get(channel_target) or channel_target
        if not webhook.startswith("http"):
            logger.warning("discord channel_target %s does not look like a webhook URL", channel_target)
            return
        payload = {"content": render_plain(post)[:1900]}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook, json=payload, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    logger.warning("discord %s: %s", resp.status, body[:200])
