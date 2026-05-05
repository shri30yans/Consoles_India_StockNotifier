"""AI-native deal curation agent — sends new deals to admin for approval."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from commerce_platform.platform.store.repos import DealRepo, ConfigSettingsRepo
from commerce_platform.platform.notify.router import ChannelRouter
from commerce_platform.platform.events.observation import Notification

logger = logging.getLogger(__name__)
tz = timezone.utc


class CuratorAgent:
    """Autonomous curator that evaluates deals and sends to admin for approval.

    Flow:
    1. Watch deals table for new entries
    2. Evaluate score vs threshold
    3. If score < threshold, send to admin with deal details
    4. Admin reviews and approves/rejects
    5. Approved deals are sent to user channels
    """

    def __init__(
        self,
        deal_repo: DealRepo,
        config_repo: ConfigSettingsRepo,
        router: ChannelRouter,
    ):
        self._deal_repo = deal_repo
        self._config_repo = config_repo
        self._router = router

    async def curate(self) -> dict:
        """Review pending deals, send low-confidence to admin."""
        threshold = await self._config_repo.get("deals.scoring.threshold", 0.40)

        # Get deals that were created/updated in last 5 minutes and not yet reviewed by admin
        pending = await self._deal_repo.get_pending_approval(minutes=5)

        results = {
            "total_pending": len(pending),
            "sent_to_admin": 0,
            "errors": [],
        }

        admin_channel = await self._config_repo.get("deals.curation.admin_channel", "admin")

        for deal in pending:
            try:
                if deal.score < threshold:
                    # Send to admin for approval
                    msg = await self._format_approval_request(deal)
                    await self._router.send(admin_channel, msg)
                    results["sent_to_admin"] += 1

                    logger.info(f"Sent deal {deal.product_url} to admin (score: {deal.score:.2f})")
                else:
                    # Auto-approve high-confidence deals (curator auto-approve: user_id=None)
                    logger.info(f"Auto-approved deal {deal.product_url} (score: {deal.score:.2f})")
                    await self._deal_repo.mark_reviewed(
                        deal.id or 0,
                        status="approved",
                        user_id=None,  # None = curator auto-approved
                    )

            except Exception as e:
                logger.exception(f"Curation failed for deal {deal.id}: {e}")
                results["errors"].append(str(e))

        return results

    async def _format_approval_request(self, deal) -> str:
        """Format deal as approval request message."""
        msg = (
            f"🔍 **New Deal Pending Approval**\n\n"
            f"**Product:** {deal.product_title or deal.product_id}\n"
            f"**Retailer:** {deal.retailer}\n"
            f"**Price:** ₹{deal.price_paise / 100:,.0f}"
        )

        if deal.mrp_paise:
            msg += f" (MRP: ₹{deal.mrp_paise / 100:,.0f})"

        if deal.discount_pct:
            msg += f"\n**Discount:** {deal.discount_pct * 100:.0f}% off"

        msg += f"\n**Score:** {deal.score:.2%}"
        msg += f"\n**Reason:** {', '.join(deal.score_reasons)}"
        msg += f"\n**Source:** {deal.source}"
        msg += f"\n\n**[View Deal →]({deal.product_url})**"
        msg += f"\n\n`/approve {deal.id}` — Accept\n`/reject {deal.id}` — Decline"

        return msg

    async def approve_deal(self, deal_id: int, user_id: int | None = None, reason: str | None = None) -> bool:
        """Admin approves a deal → mark as approved, send to channels."""
        deal = await self._deal_repo.get_by_id(deal_id)
        if not deal:
            return False

        # Mark approved
        await self._deal_repo.mark_reviewed(
            deal_id,
            status="approved",
            user_id=user_id,
            reason=reason,
        )

        logger.info(f"Deal {deal_id} approved by user {user_id}")
        return True

    async def reject_deal(self, deal_id: int, reason: str | None = None, user_id: int | None = None) -> bool:
        """Admin rejects a deal."""
        deal = await self._deal_repo.get_by_id(deal_id)
        if not deal:
            return False

        await self._deal_repo.mark_reviewed(
            deal_id,
            status="rejected",
            user_id=user_id,
            reason=reason,
        )

        logger.info(f"Deal {deal_id} rejected by user {user_id}: {reason}")
        return True
