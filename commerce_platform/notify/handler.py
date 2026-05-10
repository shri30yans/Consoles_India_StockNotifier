"""Notification handler — formats and sends rule matches to channels."""

from __future__ import annotations

import logging

from commerce_platform.platform.events.observation import Notification, RuleMatch
from commerce_platform.platform.notify.affiliate import AffiliateRewriter
from commerce_platform.platform.notify.router import ChannelRouter

logger = logging.getLogger(__name__)

# Notification rule types (transformed from Rule types during RuleMatch creation)
NOTIF_TYPE_STOCK = "stock"
NOTIF_TYPE_PRICE = "price"
NOTIF_TYPE_DEAL = "deal"


class NotificationHandler:
    """Handles rule matches → format → send to channels."""

    def __init__(self, router: ChannelRouter, affiliate_rewriter: AffiliateRewriter | None = None) -> None:
        self._router = router
        self._affiliate = affiliate_rewriter

    async def handle_rule_match(self, match: RuleMatch) -> None:
        """Process a single rule match and send notification."""
        notification = await self._format_notification(match)

        logger.info(
            "Sending notification: product=%s rule=%s channels=%s",
            notification.product_id,
            notification.rule_id,
            notification.target_channels,
        )

        for channel_id in notification.target_channels:
            try:
                await self._router.send(channel_id, notification.body)
            except Exception as e:
                logger.exception(
                    "Failed to send to channel %s: %s",
                    channel_id,
                    e,
                )

    async def _format_notification(self, match: RuleMatch) -> Notification:
        """Create markdown notification from rule match."""
        obs = match.observation
        discount = match.discount_percent()

        if match.rule_type == NOTIF_TYPE_STOCK:
            status = "✅ IN STOCK" if obs.in_stock else "❌ OUT OF STOCK"
            title = f"{obs.product_title or obs.product_id}: {status}"
            body = await self._format_body(
                title=title,
                product_id=obs.product_id,
                retailer=obs.retailer,
                price=obs.price_paise / 100 if obs.price_paise > 0 else None,
                url=obs.product_url,
            )
            price_rupees = obs.price_paise / 100 if obs.price_paise > 0 else None

        elif match.rule_type == NOTIF_TYPE_PRICE:
            price_rupees = obs.price_paise / 100
            title = f"{obs.product_title or obs.product_id}: ₹{price_rupees:,.0f}"
            threshold = match.context.get("threshold_inr")
            body = await self._format_body(
                title=title,
                product_id=obs.product_id,
                retailer=obs.retailer,
                price=price_rupees,
                threshold=threshold,
                url=obs.product_url,
            )

        elif match.rule_type == NOTIF_TYPE_DEAL:
            price_rupees = obs.price_paise / 100
            discount_pct = match.context.get("discount_pct", 0)
            title = f"{obs.product_title or obs.product_id}: {discount_pct:.0%} off · ₹{price_rupees:,.0f}"
            body = await self._format_body(
                title=title,
                product_id=obs.product_id,
                retailer=obs.retailer,
                price=price_rupees,
                discount_pct=discount_pct,
                url=obs.product_url,
            )

        else:
            title = f"{obs.product_id}"
            body = title
            price_rupees = obs.price_paise / 100 if obs.price_paise > 0 else None

        return Notification(
            product_id=obs.product_id,
            rule_id=match.rule_id,
            rule_type=match.rule_type,
            title=title,
            body=body,
            target_channels=match.channels,
            retailer=obs.retailer,
            price_rupees=price_rupees,
            discount_pct=discount if discount > 0 else None,
            in_stock=obs.in_stock,
            product_url=obs.product_url,
        )

    async def _format_body(
        self,
        title: str,
        product_id: str,
        retailer: str,
        price: float | None = None,
        threshold: float | None = None,
        discount_pct: float | None = None,
        url: str | None = None,
    ) -> str:
        """Format notification body as markdown."""
        lines = [f"**{title}**"]

        if price is not None:
            lines.append(f"**Price:** ₹{price:,.0f}")

        if threshold is not None:
            lines.append(f"**Threshold:** ₹{threshold:,.0f}")

        if discount_pct is not None:
            lines.append(f"**Discount:** {discount_pct:.0%}")

        lines.append(f"**Retailer:** {retailer}")

        if url:
            # Rewrite URL with affiliate tag if available
            if self._affiliate:
                url = await self._affiliate.rewrite(url, retailer) or url
            lines.append(f"[View on {retailer.title()}]({url})")

        return "\n".join(lines)
