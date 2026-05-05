"""Agent gateway — REST API for decoupled agent communication.

Agents (Hermes-based) call these endpoints to report results:
- POST /deals/discover → Report discovered deals
- POST /deals/parser-error → Report parser failure
- POST /deals/alert → Alert on suspicious activity
- GET /deals/pending → Fetch pending deals for review

Core system publishes events:
- EVENT: parser.failed → Triggers ParserFixerAgent
- EVENT: deal.created → Triggers CuratorAgent
- EVENT: retailer.discovered → Triggers analysis
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.store.repos import DealRepo, ConfigSettingsRepo
from commerce_platform.stock.sources.serp_parsers import ListingItem

logger = logging.getLogger(__name__)
tz = timezone.utc


class ParserErrorReport(BaseModel):
    """Agent reports: parser failed, here's the HTML and error."""

    source_type: str = Field(..., description="amazon_deals, flipkart_deals, etc.")
    seed_url: str
    error_message: str
    html_snippet: str = Field(..., description="First 10KB of HTML where error occurred")
    attempted_selector: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(tz).isoformat())


class ParserSuccessReport(BaseModel):
    """Agent reports: discovered deals."""

    source_type: str
    seed_url: str
    items: list[dict[str, Any]]  # ListingItem as dict
    items_qualified: int  # After pre-filter
    timestamp: str = Field(default_factory=lambda: datetime.now(tz).isoformat())


class FraudAlertReport(BaseModel):
    """Agent reports: suspicious deal detected."""

    deal_id: int | None
    product_url: str
    reason: str  # "price_below_cost", "seller_unknown", "fake_ratings"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: dict[str, Any]  # details for human review
    timestamp: str = Field(default_factory=lambda: datetime.now(tz).isoformat())


@dataclass
class AgentGatewayEvent:
    """Events published when agents report results."""

    event_type: Literal["parser.failed", "parser.success", "fraud.alert"]
    agent_name: str
    payload: Any
    timestamp: str = Field(default_factory=lambda: datetime.now(tz).isoformat())


class AgentGateway:
    """Endpoint handler for agent communication.

    Agents are independent processes that:
    1. Call POST /deals/discover to report findings
    2. Call POST /deals/parser-error to report failures
    3. Listen for EVENT: parser.failed to trigger self-healing

    This gateway decouples agent logic from core system.
    """

    def __init__(
        self,
        deal_repo: DealRepo,
        config_repo: ConfigSettingsRepo,
        bus: EventBus,
    ) -> None:
        self._deal_repo = deal_repo
        self._config_repo = config_repo
        self._bus = bus

    def create_router(self) -> APIRouter:
        """Create FastAPI router for agent endpoints."""
        router = APIRouter(prefix="/deals", tags=["agent-gateway"])

        @router.post("/discover")
        async def agent_report_discovery(report: ParserSuccessReport) -> dict:
            """Agent reports: I discovered N items from this retailer."""
            logger.info(
                "Agent discovery: %s found %d items (%d qualified)",
                report.source_type,
                len(report.items),
                report.items_qualified,
            )

            deals_created = 0
            deals_updated = 0

            # Process each item
            for item_dict in report.items:
                try:
                    # Item already scored by agent, just store it
                    from commerce_platform.platform.store.repos.deal_repo import DealRow

                    deal_row = DealRow(
                        id=None,
                        product_url=item_dict.get("url"),
                        product_id=item_dict.get("product_id"),
                        retailer=item_dict.get("retailer"),
                        price_paise=item_dict.get("price_paise"),
                        mrp_paise=item_dict.get("mrp_paise"),
                        discount_pct=item_dict.get("discount_pct"),
                        score=item_dict.get("score", 0.0),
                        score_reasons=item_dict.get("score_reasons", []),
                        product_title=item_dict.get("product_title"),
                        image_url=item_dict.get("image_url"),
                        source=f"agent:{report.source_type}",
                        is_active=True,
                        last_notified_at=None,
                        first_seen_at=report.timestamp,
                        last_confirmed_at=report.timestamp,
                    )

                    action, _should_notify = await self._deal_repo.upsert(deal_row)

                    if action == "inserted":
                        deals_created += 1
                    elif action in ("price_improved", "reactivated"):
                        deals_updated += 1

                except Exception as e:
                    logger.exception("Failed to process item from agent: %s", e)

            # Publish event for downstream processors
            await self._bus.publish(
                AgentGatewayEvent(
                    event_type="parser.success",
                    agent_name=report.source_type,
                    payload={
                        "items_found": len(report.items),
                        "items_qualified": report.items_qualified,
                        "deals_created": deals_created,
                        "deals_updated": deals_updated,
                    },
                )
            )

            return {
                "stored": deals_created + deals_updated,
                "created": deals_created,
                "updated": deals_updated,
            }

        @router.post("/parser-error")
        async def agent_report_parser_error(report: ParserErrorReport) -> dict:
            """Agent reports: parser failed. System triggers ParserFixerAgent."""
            logger.warning(
                "Parser error reported: %s from %s — %s",
                report.source_type,
                report.seed_url,
                report.error_message,
            )

            # Store error for analysis
            await self._config_repo.set(
                f"parser.error.{report.source_type}.latest",
                json.dumps(
                    {
                        "seed_url": report.seed_url,
                        "error": report.error_message,
                        "attempted_selector": report.attempted_selector,
                        "html_length": len(report.html_snippet),
                        "timestamp": report.timestamp,
                    }
                ),
            )

            # Publish event (ParserFixerAgent subscribes)
            await self._bus.publish(
                AgentGatewayEvent(
                    event_type="parser.failed",
                    agent_name=report.source_type,
                    payload={
                        "error": report.error_message,
                        "seed_url": report.seed_url,
                        "html_length": len(report.html_snippet),
                    },
                )
            )

            return {
                "ack": True,
                "message": "ParserFixerAgent will analyze this failure",
            }

        @router.post("/alert")
        async def agent_report_fraud_alert(report: FraudAlertReport) -> dict:
            """Agent reports: suspicious deal detected."""
            logger.warning(
                "Fraud alert: %s (confidence: %.1f%%) — %s",
                report.product_url,
                report.confidence * 100,
                report.reason,
            )

            # Store alert for admin review
            await self._config_repo.set(
                f"fraud.alert.{datetime.now(tz).timestamp()}",
                json.dumps(
                    {
                        "product_url": report.product_url,
                        "reason": report.reason,
                        "confidence": report.confidence,
                        "evidence": report.evidence,
                    }
                ),
            )

            # Publish event
            await self._bus.publish(
                AgentGatewayEvent(
                    event_type="fraud.alert",
                    agent_name="FraudDetectionAgent",
                    payload={
                        "url": report.product_url,
                        "reason": report.reason,
                        "confidence": report.confidence,
                    },
                )
            )

            return {"ack": True, "for_admin_review": True}

        return router
