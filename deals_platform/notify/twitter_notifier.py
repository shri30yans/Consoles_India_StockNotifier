from __future__ import annotations

import asyncio
import logging
import os

from deals_platform.domain.events import PublishablePost
from deals_platform.notify.formatting import render_tweet

logger = logging.getLogger(__name__)


class TwitterNotifier:
    name = "twitter"

    def __init__(self) -> None:
        self._ck = os.environ.get("consumer_key")
        self._cs = os.environ.get("consumer_secret")
        self._at = os.environ.get("access_token")
        self._ats = os.environ.get("access_token_secret")

    async def send(self, post: PublishablePost, channel_target: str) -> None:
        if not all([self._ck, self._cs, self._at, self._ats]):
            logger.warning("Twitter creds missing; skipping")
            return
        await asyncio.get_running_loop().run_in_executor(None, self._post, render_tweet(post))

    def _post(self, text: str) -> None:
        try:
            import tweepy

            client = tweepy.Client(
                consumer_key=self._ck,
                consumer_secret=self._cs,
                access_token=self._at,
                access_token_secret=self._ats,
            )
            client.create_tweet(text=text)
        except Exception:
            logger.exception("twitter post failed")
