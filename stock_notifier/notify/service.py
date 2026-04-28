from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime

import aiohttp
import tweepy
from pytz import timezone

from stock_notifier.models import AppConfig, ProductConfig, StockSignal, WebsiteConfig
from stock_notifier.stock_state import ContinuousStockState

logger = logging.getLogger(__name__)

_TELEGRAM_RETRIES = 4
_TELEGRAM_BACKOFF_BASE = 1.5


class NotificationService:
    """Side effects for in-stock transitions (Telegram + Twitter)."""

    def __init__(
        self,
        app: AppConfig,
        products: dict[str, ProductConfig],
        websites: dict[str, WebsiteConfig],
        state: ContinuousStockState,
    ) -> None:
        self._app = app
        self._products = products
        self._websites = websites
        self._state = state
        self._telegram_token = os.getenv("TELEGRAM_TOKEN")
        self._consumer_key = os.getenv("consumer_key")
        self._consumer_secret = os.getenv("consumer_secret")
        self._access_token = os.getenv("access_token")
        self._access_token_secret = os.getenv("access_token_secret")

    async def apply(self, signal: StockSignal, page) -> None:
        if not signal.in_stock:
            self._state.set_in_stock(signal.product_key, signal.website_key, False)
            return

        was_hot = self._state.is_continuously_in_stock(signal.product_key, signal.website_key)
        if not was_hot and self._app.notify:
            await self._dispatch(signal, page)
        self._state.set_in_stock(signal.product_key, signal.website_key, True)

    async def _dispatch(self, signal: StockSignal, page) -> None:
        product = self._products.get(signal.product_key)
        website = self._websites.get(signal.website_key)
        if product is None:
            logger.error("Unknown product %s for notification", signal.product_key)
            return
        if website is None:
            logger.error("Unknown website %s for notification", signal.website_key)
            return

        logger.info("%s in stock at %s (%s)", signal.product_key, signal.website_key, signal.method)
        print(f"{signal.product_key} in stock at {signal.website_key}.")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: _twitter_post(
                self._consumer_key,
                self._consumer_secret,
                self._access_token,
                self._access_token_secret,
                website,
                product,
                self._app.amazon_affiliate_tag,
            ),
        )
        await _telegram_post_with_retries(
            self._telegram_token,
            self._app.telegram_chat_id,
            website,
            product,
            self._app.amazon_affiliate_tag,
        )


def _twitter_post(
    consumer_key: str | None,
    consumer_secret: str | None,
    access_token: str | None,
    access_token_secret: str | None,
    website: WebsiteConfig,
    product: ProductConfig,
    affiliate_tag: str,
) -> None:
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        return

    primary = (product.affiliate_links or {}).get(website.key) or (product.links or {}).get(
        website.key
    )
    message = f"❗ {product.display_name} in stock at {website.display_name}! {primary or ''}\n"

    if website.key == "amazon":
        atc = (product.add_to_cart_links or {}).get(website.key)
        if atc:
            message += f"🛒 Add to cart: {atc}\n"
        if product.wishlist:
            message += f"📜 Wishlist: {product.wishlist}?tag={affiliate_tag}\n"

    ist = datetime.now(timezone("Asia/Kolkata")).strftime("%d-%m-%y • %H:%M:%S")
    message += f"🕒 Time: {ist}\n"
    message += (product.twitter_hashtags or "") + " #ConsolesIndia"

    try:
        client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        client.create_tweet(text=message)
        return
    except Exception as e:
        logger.info("Twitter X API v2 path failed (%s); trying legacy 1.1 API", e)

    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        api.update_status(message)
    except Exception as e:
        logger.warning("Twitter post failed: %s", e)


async def _telegram_post_with_retries(
    token: str | None,
    chat_id: str,
    website: WebsiteConfig,
    product: ProductConfig,
    affiliate_tag: str,
) -> None:
    if not token:
        return
    primary = (product.affiliate_links or {}).get(website.key) or (product.links or {}).get(
        website.key
    )
    text = f"❗ [{product.display_name} in stock at {website.display_name}!]({primary or ''})\n"
    if website.key == "amazon" and product.wishlist:
        text += f"[📜 Wishlist]({product.wishlist}?tag={affiliate_tag})\n"
    ist = datetime.now(timezone("Asia/Kolkata")).strftime("%d-%m-%y • %H:%M:%S")
    text += f"🕒 Time: {ist}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    last_status: int | None = None
    for attempt in range(_TELEGRAM_RETRIES):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    last_status = response.status
                    if response.status < 400:
                        return
                    body = await response.text()
                    snippet = (body[:200] + "…") if len(body) > 200 else body
                    logger.warning(
                        "Telegram HTTP %s (attempt %s): %s", response.status, attempt + 1, snippet
                    )
        except asyncio.TimeoutError:
            logger.warning("Telegram timeout (attempt %s)", attempt + 1)

        if attempt < _TELEGRAM_RETRIES - 1:
            await asyncio.sleep(_TELEGRAM_BACKOFF_BASE**attempt)

    logger.error("Telegram send failed after retries (last HTTP %s)", last_status)
