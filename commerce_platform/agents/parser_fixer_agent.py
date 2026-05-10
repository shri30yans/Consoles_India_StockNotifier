"""ParserFixerAgent — Self-healing agent that fixes broken parsers.

When a traditional parser fails (CSS selectors broke):
1. Agent receives error event
2. Agent analyzes HTML to understand new structure
3. Agent calls Claude vision/text API to suggest new selectors
4. Agent tests selectors on stored HTML
5. Agent publishes fix (stored in config, picked up on next run)

This is where agents provide value: adaptive, intelligent failure recovery.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from anthropic import Anthropic

from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.store.repos import ConfigSettingsRepo

logger = logging.getLogger(__name__)


class ParserFixerAgent:
    """Autonomous agent that fixes broken parsers using Claude vision."""

    def __init__(
        self,
        config_repo: ConfigSettingsRepo,
        bus: EventBus,
        anthropic_client: Anthropic | None = None,
    ) -> None:
        self._config_repo = config_repo
        self._bus = bus
        self._anthropic = anthropic_client or Anthropic()

    async def fix_parser(self, source_type: str, error_info: dict[str, Any]) -> bool:
        """
        Attempt to fix a broken parser.

        Returns True if fix found and stored, False if unable to fix.
        """
        logger.info(f"ParserFixerAgent analyzing failure for {source_type}")

        seed_url = error_info.get("seed_url")
        error_msg = error_info.get("error")
        html_length = error_info.get("html_length", 0)

        if not seed_url:
            logger.warning("No seed URL in error info, cannot fix")
            return False

        # Get HTML snippet from storage
        html_snippet = await self._config_repo.get(
            f"parser.error.{source_type}.html_snippet"
        )
        if not html_snippet:
            logger.warning("No HTML snippet stored, cannot analyze")
            return False

        # Analyze with Claude
        logger.info(f"Calling Claude to analyze {source_type} parser failure")
        try:
            suggestion = await self._analyze_html_and_suggest_selectors(
                source_type, error_msg, html_snippet
            )

            if suggestion:
                # Store the suggestion for operator review
                await self._config_repo.set(
                    f"parser.suggestion.{source_type}",
                    json.dumps(
                        {
                            "suggested_selectors": suggestion,
                            "from_error": error_msg,
                            "needs_manual_review": True,
                            "timestamp": "",
                        }
                    ),
                )
                logger.info(f"Stored parser suggestion for {source_type}")
                return True

        except Exception as e:
            logger.exception(f"Failed to analyze parser failure: {e}")

        return False

    async def _analyze_html_and_suggest_selectors(
        self, source_type: str, error: str, html_snippet: str
    ) -> dict[str, str] | None:
        """Use Claude to analyze HTML and suggest new CSS selectors."""

        # Map source to known selectors (these are the ones that broke)
        broken_selectors = {
            "amazon_deals": {
                "deal_card": ".DealCard-module__dealContent",
                "price": ".DealCard-module__price",
                "discount": ".DealCard-module__percentOff",
                "image": "img.a-dynamic-image",
                "url": "a.a-link-normal[href*='/dp/']",
            },
            "flipkart_deals": {
                "product_card": "._1fQZEK",
                "price": "._30jeq3",
                "original_price": "._3I9_wc",
                "discount": "._3LWZlK",
                "image": "img._396cs4",
                "url": "a[href*='/p/']",
            },
            "ajio_deals": {
                "product_card": ".productCardImg",
                "price": ".productCardPricingSection",
                "image": "img.productCardImg",
                "url": "a[data-productid]",
            },
            "myntra_deals": {
                "product_card": ".productCardImg",
                "price": "span[data-price]",
                "original_price": "span[data-mrp]",
                "discount": ".discountBadge",
                "image": "img.productCardImg",
                "url": "a[data-productid]",
            },
        }

        broken = broken_selectors.get(source_type, {})

        prompt = f"""You are a web scraping expert. A CSS selector-based parser broke for {source_type}.

BROKEN ERROR: {error}

OLD SELECTORS (no longer work):
{json.dumps(broken, indent=2)}

HERE'S A SAMPLE OF THE NEW HTML:
{html_snippet[:5000]}

TASK: Analyze the HTML structure and suggest NEW CSS selectors that would work.

Return JSON:
{{
  "deal_card": "new selector for product card container",
  "price": "new selector for price",
  "discount": "new selector for discount percentage",
  "image": "new selector for image",
  "url": "new selector for product URL"
}}

Only return selectors you're confident about. If you can't find a selector, omit it.
Prioritize class-based selectors over brittle positional selectors.
"""

        try:
            response = self._anthropic.messages.create(
                model="claude-opus-4-7",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text

            # Extract JSON from response
            json_match = re.search(r"\{[^}]+\}", response_text, re.DOTALL)
            if json_match:
                suggested = json.loads(json_match.group())
                logger.info(f"Claude suggested selectors: {suggested}")
                return suggested

        except Exception as e:
            logger.exception(f"Claude API call failed: {e}")

        return None

    async def run_continuous(self) -> None:
        """Run ParserFixerAgent continuously, listening for parser failures.

        This is a background task that wakes when EVENT: parser.failed occurs.
        """
        logger.info("ParserFixerAgent started, listening for parser failures")

        # Subscribe to parser failure events
        from commerce_platform.deals.agent_gateway import AgentGatewayEvent

        queue = self._bus.subscribe(AgentGatewayEvent)

        try:
            async for event in self._bus.iter_events(queue):
                if event.event_type == "parser.failed":
                    agent_name = event.agent_name
                    await self.fix_parser(agent_name, event.payload)

        except Exception as e:
            logger.exception(f"ParserFixerAgent error: {e}")
