"""Telegram notifier — sends plain text or Markdown to a chat ID."""

from __future__ import annotations

import logging
import os

from commerce_platform.platform.notify._http_channel import BaseHttpChannel, ChannelError
from commerce_platform.platform.notify.retry import with_retries

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseHttpChannel):
    def __init__(self, *, token: str | None = None, retries: int = 4) -> None:
        self._token = token or os.environ.get("TELEGRAM_TOKEN", "")
        self._retries = retries

    async def send(self, text: str, chat_id: str) -> None:
        if not self._token:
            logger.warning("TELEGRAM_TOKEN missing; skipping notification")
            return

        resolved_chat = os.environ.get(chat_id, chat_id) if chat_id.startswith("env:") else chat_id
        # Also handle already-resolved env vars passed as raw env var names
        if not resolved_chat.lstrip("-").isdigit() and not resolved_chat.startswith("@"):
            resolved_chat = os.environ.get(resolved_chat, resolved_chat)

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {
            "chat_id": resolved_chat,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }

        async def _send() -> None:
            try:
                await self._post_json(url, payload)
            except ChannelError as e:
                raise RuntimeError(f"Telegram {e.status}: {(e.body_preview or '')[:200]}") from e

        await with_retries(_send, retries=self._retries, label=f"telegram:{resolved_chat}")

    async def send_raw(self, payload: dict) -> dict:
        """Send arbitrary payload; returns response JSON."""
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        try:
            data = await self._post_json(url, payload, return_json=True)
        except ChannelError as e:
            raise RuntimeError(f"Telegram {e.status}: {(e.body_preview or '')[:200]}") from e
        if not isinstance(data, dict):
            raise RuntimeError(f"Telegram unexpected response: {str(data)[:200]}")
        return data.get("result") or {}
