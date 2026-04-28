from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

from deals_platform.domain.events import PublishablePost
from deals_platform.notify.formatting import render_plain

logger = logging.getLogger(__name__)


class EmailNotifier:
    name = "email"

    def __init__(self) -> None:
        self._host = os.environ.get("SMTP_HOST")
        self._port = int(os.environ.get("SMTP_PORT", "587"))
        self._user = os.environ.get("SMTP_USERNAME")
        self._pwd = os.environ.get("SMTP_PASSWORD")
        self._from = os.environ.get("SMTP_FROM")

    async def send(self, post: PublishablePost, channel_target: str) -> None:
        to = os.environ.get(channel_target) or channel_target
        if not (self._host and self._from and to):
            logger.info("email skip (creds missing)")
            return
        await asyncio.get_running_loop().run_in_executor(None, self._send_sync, to, post)

    def _send_sync(self, to: str, post: PublishablePost) -> None:
        msg = EmailMessage()
        msg["Subject"] = post.title
        msg["From"] = self._from
        msg["To"] = to
        msg.set_content(render_plain(post))
        try:
            with smtplib.SMTP(self._host, self._port) as smtp:
                smtp.starttls()
                if self._user and self._pwd:
                    smtp.login(self._user, self._pwd)
                smtp.send_message(msg)
        except Exception:
            logger.exception("email send failed")
