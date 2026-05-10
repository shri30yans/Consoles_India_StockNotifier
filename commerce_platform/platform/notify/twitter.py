"""Twitter / X notifier — posts plain text via API v2.

Prefers OAuth 2.0 user access token (Bearer) when TWITTER_OAUTH2_ACCESS_TOKEN is set;
refreshes with TWITTER_OAUTH2_REFRESH_TOKEN + TWITTER_CLIENT_ID/SECRET on 401.
Falls back to OAuth 1.0a (consumer + access token + token secret) if OAuth2 is unset.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re

import aiohttp
import tweepy

from commerce_platform.platform.notify._http_channel import BaseHttpChannel, ChannelError
from commerce_platform.platform.notify.retry import with_retries

logger = logging.getLogger(__name__)

_DEFAULT_MAX_LEN = 280
_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
_TWEETS_URL = "https://api.twitter.com/2/tweets"


def markdown_to_plain_x(text: str, *, max_len: int | None = None) -> str:
    """Strip Telegram-style markdown for X; keep one URL per line readable."""
    limit = max_len
    if limit is None:
        try:
            limit = int(os.environ.get("TWITTER_MAX_TWEET_LENGTH", str(_DEFAULT_MAX_LEN)))
        except ValueError:
            limit = _DEFAULT_MAX_LEN

    s = text.replace("**", "")
    s = re.sub(r"\[([^\]]*)\]\((https?://[^)]+)\)", r"\1 \2", s)
    s = s.strip()
    if len(s) > limit:
        s = s[: max(0, limit - 1)].rstrip() + "…"
    return s


def _oauth1_credentials() -> tuple[str, str, str, str]:
    ck = (
        os.environ.get("TWITTER_CONSUMER_KEY", "")
        or os.environ.get("consumer_key", "")
    ).strip()
    cs = (
        os.environ.get("TWITTER_CONSUMER_SECRET", "")
        or os.environ.get("consumer_secret", "")
    ).strip()
    at = (
        os.environ.get("TWITTER_ACCESS_TOKEN", "")
        or os.environ.get("access_token", "")
    ).strip()
    ats = (
        os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")
        or os.environ.get("access_token_secret", "")
    ).strip()
    return ck, cs, at, ats


class TwitterNotifier(BaseHttpChannel):
    """Post as the authenticated user (OAuth 2.0 user Bearer preferred, else OAuth 1.0a)."""

    def __init__(self, *, retries: int = 4) -> None:
        super().__init__()
        self._retries = retries
        self._oauth2_access_mem: str | None = None
        self._oauth2_refresh_mem: str | None = None

    def _oauth2_access(self) -> str | None:
        if self._oauth2_access_mem:
            return self._oauth2_access_mem
        t = os.environ.get("TWITTER_OAUTH2_ACCESS_TOKEN", "").strip()
        return t or None

    def _oauth2_refresh(self) -> str | None:
        if self._oauth2_refresh_mem is not None:
            return self._oauth2_refresh_mem or None
        t = os.environ.get("TWITTER_OAUTH2_REFRESH_TOKEN", "").strip()
        return t or None

    def _client_oauth1(self) -> tweepy.Client | None:
        ck, cs, at, ats = _oauth1_credentials()
        if not all((ck, cs, at, ats)):
            return None
        return tweepy.Client(
            consumer_key=ck,
            consumer_secret=cs,
            access_token=at,
            access_token_secret=ats,
        )

    async def _refresh_oauth2_user_token(self) -> bool:
        refresh = self._oauth2_refresh()
        cid = os.environ.get("TWITTER_CLIENT_ID", "").strip()
        csec = os.environ.get("TWITTER_CLIENT_SECRET", "").strip()
        if not all([refresh, cid, csec]):
            logger.error(
                "Twitter OAuth2 refresh needs TWITTER_OAUTH2_REFRESH_TOKEN, "
                "TWITTER_CLIENT_ID, and TWITTER_CLIENT_SECRET",
            )
            return False

        form = {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": cid,
        }
        auth = aiohttp.BasicAuth(cid, csec)
        try:
            payload = await self._post_form_urlencoded(_TOKEN_URL, form, auth=auth)
        except ChannelError as e:
            logger.error(
                "Twitter OAuth2 refresh HTTP %s: %s",
                e.status,
                (e.body_preview or "")[:500],
            )
            return False
        except Exception:
            logger.exception("Twitter OAuth2 refresh request failed")
            return False

        new_at = payload.get("access_token")
        new_rt = payload.get("refresh_token")
        if not new_at:
            logger.error("Twitter OAuth2 refresh: no access_token in response")
            return False

        self._oauth2_access_mem = new_at
        self._oauth2_refresh_mem = new_rt if new_rt else refresh
        if new_rt and new_rt != refresh:
            logger.warning(
                "Twitter rotated the refresh token - update TWITTER_OAUTH2_REFRESH_TOKEN in .env "
                "so restarts keep working.",
            )
        logger.info("Twitter OAuth2 access token refreshed (held in memory for this process).")
        return True

    async def _send_oauth2_user(self, plain: str) -> None:
        refreshed_once = False
        last_err: BaseException | None = None
        for attempt in range(self._retries * 2):
            token = self._oauth2_access()
            if not token:
                logger.error("Twitter OAuth2: no access token")
                return
            try:
                await self._post_json(
                    _TWEETS_URL,
                    {"text": plain},
                    headers={"Authorization": f"Bearer {token}"},
                    return_json=True,
                )
                logger.info("Twitter post sent (%d chars)", len(plain))
                return
            except ChannelError as e:
                if e.status == 401:
                    if refreshed_once:
                        logger.error("Twitter OAuth2: still unauthorized after token refresh")
                        return
                    refreshed_once = True
                    logger.info("Twitter OAuth2 unauthorized - refreshing access token")
                    if not await self._refresh_oauth2_user_token():
                        return
                    continue
                last_err = e
                await asyncio.sleep(1.5 ** min(attempt, 6))
            except Exception as e:
                last_err = e
                await asyncio.sleep(1.5 ** min(attempt, 6))
        if last_err:
            logger.error("Twitter OAuth2 post failed after retries: %s", last_err)

    async def send(self, text: str) -> None:
        plain = markdown_to_plain_x(text)

        if self._oauth2_access():
            await self._send_oauth2_user(plain)
            return

        client = self._client_oauth1()
        if client is None:
            logger.warning(
                "Twitter: set TWITTER_OAUTH2_ACCESS_TOKEN (+ refresh + client id/secret) "
                "or OAuth 1.0a consumer_key, consumer_secret, access_token, access_token_secret",
            )
            return

        async def _post() -> bool:
            def _sync() -> None:
                client.create_tweet(text=plain)

            await asyncio.to_thread(_sync)
            return True

        ok = await with_retries(_post, retries=self._retries, label="twitter")
        if ok:
            logger.info("Twitter post sent (%d chars)", len(plain))
