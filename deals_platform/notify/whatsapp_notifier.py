"""WhatsApp via Meta Cloud API."""

from __future__ import annotations

import logging
import os

import aiohttp

from deals_platform.domain.events import PublishablePost
from deals_platform.notify.formatting import render_plain

logger = logging.getLogger(__name__)


class WhatsAppNotifier:
    name = "whatsapp"

    def __init__(self) -> None:
        self._phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
        self._token = os.environ.get("WHATSAPP_ACCESS_TOKEN")

    async def send(self, post: PublishablePost, channel_target: str) -> None:
        if not (self._phone_id and self._token):
            logger.warning("WhatsApp creds missing; skipping send")
            return
        to = os.environ.get(channel_target) or channel_target
        url = f"https://graph.facebook.com/v20.0/{self._phone_id}/messages"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"preview_url": True, "body": render_plain(post)},
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    logger.warning("whatsapp %s: %s", resp.status, body[:200])
