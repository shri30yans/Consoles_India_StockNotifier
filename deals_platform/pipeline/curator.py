"""AI curation agent.

Given a ScoredDeal, the agent:
  1. Drops it if recently posted (cooldown via PostLog)
  2. Asks the LLM to (a) classify category, (b) write a 2-line post,
     (c) decide whether to publish or hold
  3. Builds the final affiliate URL
  4. Returns a PublishablePost

The LLM is constrained to JSON output. If the LLM fails, we fall back to a
deterministic template — the platform never blocks on the LLM.
"""

from __future__ import annotations

import json
import logging
from typing import Mapping

from deals_platform.domain.events import PublishablePost, ScoredDeal
from deals_platform.domain.models import Category
from deals_platform.domain.ports import LLMClient, PostLog
from deals_platform.pipeline.affiliate import build_affiliate_url

logger = logging.getLogger(__name__)


_SYSTEM = (
    "You are an AI editor for an Indian deals channel. You write concise, "
    "honest, no-hype deal posts in friendly Indian English. Never exaggerate. "
    "Never invent facts. Output ONLY valid JSON matching the requested schema."
)

_SCHEMA_HINT = (
    '{"publish": bool, "category": "tech|gaming|lifestyle|home|beauty|baby|grocery", '
    '"title": str (<=80 chars), "body_markdown": str (<=400 chars, '
    'use **bold** for the price, include 1 emoji max), "skip_reason": str|null}'
)


class CuratorAgent:
    def __init__(
        self,
        llm: LLMClient,
        post_log: PostLog,
        category_to_channels: Mapping[str, tuple[str, ...]],
        *,
        repost_cooldown_hours: int = 24,
        score_threshold: float = 0.55,
    ) -> None:
        self._llm = llm
        self._post_log = post_log
        self._cat_channels = category_to_channels
        self._cooldown = repost_cooldown_hours
        self._threshold = score_threshold

    async def curate(self, scored: ScoredDeal) -> PublishablePost | None:
        if scored.breakdown.score < self._threshold:
            return None

        if await self._post_log.recently_posted(scored.deal.canonical_id, self._cooldown):
            logger.info(
                "skip %s — posted within last %dh", scored.deal.canonical_id, self._cooldown
            )
            return None

        decision = await self._ask_llm(scored)
        if decision is None or not decision.get("publish", False):
            logger.info("LLM held back %s: %s", scored.deal.canonical_id, decision)
            return None

        try:
            category = Category(decision.get("category", "unknown"))
        except ValueError:
            category = Category.UNKNOWN

        title = (decision.get("title") or scored.deal.title)[:120]
        body = decision.get("body_markdown") or _fallback_body(scored)
        channels = self._cat_channels.get(category.value, ())
        if not channels:
            channels = self._cat_channels.get("unknown", ())

        affiliate_url = build_affiliate_url(
            scored.deal.candidate.retailer, scored.deal.candidate.product_url
        )

        return PublishablePost(
            scored=scored,
            category=category,
            target_channels=tuple(channels),
            title=title,
            body_markdown=body,
            affiliate_url=affiliate_url,
            image_url=scored.deal.image_url,
        )

    async def _ask_llm(self, scored: ScoredDeal) -> dict | None:
        ctx = _format_context(scored)
        try:
            return await self._llm.complete_json(
                system=_SYSTEM,
                user=ctx,
                schema_hint=_SCHEMA_HINT,
                max_tokens=400,
                temperature=0.4,
            )
        except Exception:
            logger.exception("LLM curation failed; falling back to template")
            return {
                "publish": True,
                "category": "unknown",
                "title": scored.deal.title[:80],
                "body_markdown": _fallback_body(scored),
                "skip_reason": None,
            }


def _format_context(scored: ScoredDeal) -> str:
    d = scored.deal
    lines = [
        f"Title: {d.title}",
        f"Retailer: {d.candidate.retailer}",
        f"URL: {d.candidate.product_url}",
        f"Current price: {d.snapshot.price}",
        f"MRP: {d.snapshot.mrp}" if d.snapshot.mrp else "MRP: unknown",
        f"90-day min: {d.history_min_90d}" if d.history_min_90d else "90-day min: unknown",
        f"30-day median: {d.history_median_30d}" if d.history_median_30d else "30-day median: unknown",
        f"Cross-retailer min: {d.cross_retailer_min}" if d.cross_retailer_min else "Cross-retailer min: unknown",
        f"Score: {scored.breakdown.score:.2f}",
        "Reasons: " + " | ".join(scored.breakdown.reasons or ("none",)),
        "",
        "Decide if this is a genuinely good deal worth posting (publish=true) "
        "or if it should be skipped (publish=false). If publishing, write a "
        "punchy 2-line post that mentions the price and ONE concrete reason "
        "(lowest in 90d, % below median, etc). Pick the most appropriate "
        "category. Output ONLY JSON.",
    ]
    return "\n".join(lines)


def _fallback_body(scored: ScoredDeal) -> str:
    d = scored.deal
    parts = [f"**{d.snapshot.price}** at {d.candidate.retailer.title()}"]
    if scored.breakdown.reasons:
        parts.append("· " + scored.breakdown.reasons[0])
    return "🔥 " + " ".join(parts)
