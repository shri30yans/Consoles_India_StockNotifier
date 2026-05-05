"""Rule engine — evaluates observations against all rules."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from commerce_platform.platform.events.observation import PriceObservation, RuleMatch
from commerce_platform.platform.store.repos import CatalogRepo, PriceRepo, StockRepo

logger = logging.getLogger(__name__)

# Rule type constants for type-safe rule evaluation
RULE_TYPE_STOCK = "stock"
RULE_TYPE_PRICE_BELOW = "price_below"
RULE_TYPE_DISCOUNT_PCT = "discount_pct"


@dataclass(frozen=True)
class Rule:
    """A single notification rule."""

    rule_id: str
    product_id: str
    rule_type: Literal["stock", "price_below", "discount_pct"]
    threshold_inr: float | None
    threshold_pct: float | None
    channels: list[str]
    retailers: list[str] | None  # None = all retailers


class RuleEngine:
    """Evaluates observations against configured rules."""

    def __init__(
        self,
        catalog_repo: CatalogRepo,
        price_repo: PriceRepo,
        stock_repo: StockRepo,
    ) -> None:
        self._catalog_repo = catalog_repo
        self._price_repo = price_repo
        self._stock_repo = stock_repo
        self._rules_cache: dict[str, list[Rule]] = {}  # product_id → rules
        self._last_stock_state: dict[tuple[str, str], bool] = {}  # (product_id, retailer) → in_stock

    async def reload_rules(self) -> None:
        """Reload all rules from database."""
        rule_dicts = await self._catalog_repo.list_all_rules()
        self._rules_cache = {}
        for rule_dict in rule_dicts:
            rule = Rule(
                rule_id=rule_dict["rule_id"],
                product_id=rule_dict["product_id"],
                rule_type=rule_dict["rule_type"],
                threshold_inr=rule_dict.get("threshold_inr"),
                threshold_pct=rule_dict.get("threshold_pct"),
                channels=rule_dict["channels"],
                retailers=rule_dict.get("retailers"),
            )
            product_id = rule.product_id
            if product_id not in self._rules_cache:
                self._rules_cache[product_id] = []
            self._rules_cache[product_id].append(rule)
        logger.info("Reloaded %d rules from database", sum(len(r) for r in self._rules_cache.values()))

    async def evaluate(self, observation: PriceObservation) -> list[RuleMatch]:
        """Check which rules match this observation. Returns list of matches."""
        if observation.product_id not in self._rules_cache:
            return []

        matches = []
        rules = self._rules_cache[observation.product_id]

        for rule in rules:
            # Check retailer filter
            if rule.retailers and observation.retailer not in rule.retailers:
                continue

            # Evaluate rule type
            if rule.rule_type == RULE_TYPE_STOCK:
                match = await self._evaluate_stock_rule(observation, rule)
            elif rule.rule_type == RULE_TYPE_PRICE_BELOW:
                match = await self._evaluate_price_below_rule(observation, rule)
            elif rule.rule_type == RULE_TYPE_DISCOUNT_PCT:
                match = await self._evaluate_discount_rule(observation, rule)
            else:
                logger.warning("Unknown rule type: %s", rule.rule_type)
                continue

            if match:
                matches.append(match)

        return matches

    async def _evaluate_stock_rule(self, observation: PriceObservation, rule: Rule) -> RuleMatch | None:
        """Stock rule: triggers when in_stock changes."""
        key = (observation.product_id, observation.retailer)
        prev_in_stock = self._last_stock_state.get(key)
        self._last_stock_state[key] = observation.in_stock

        # Trigger if: was out, now in (back in stock) OR was in, now out (out of stock)
        if prev_in_stock is None:
            return None

        if prev_in_stock != observation.in_stock:
            return RuleMatch(
                observation=observation,
                rule_id=rule.rule_id,
                rule_type="stock",
                channels=rule.channels,
                context={
                    "previous_in_stock": prev_in_stock,
                    "current_in_stock": observation.in_stock,
                },
            )

        return None

    async def _evaluate_price_below_rule(self, observation: PriceObservation, rule: Rule) -> RuleMatch | None:
        """Price below rule: triggers if price < threshold."""
        if rule.threshold_inr is None:
            return None

        threshold_paise = int(rule.threshold_inr * 100)
        if observation.price_paise > 0 and observation.price_paise <= threshold_paise:
            return RuleMatch(
                observation=observation,
                rule_id=rule.rule_id,
                rule_type="price",
                channels=rule.channels,
                context={
                    "threshold_inr": rule.threshold_inr,
                    "current_price": observation.price_paise / 100,
                },
            )

        return None

    async def _evaluate_discount_rule(self, observation: PriceObservation, rule: Rule) -> RuleMatch | None:
        """Discount rule: triggers if price is X% below MRP."""
        if rule.threshold_pct is None or observation.mrp_paise is None:
            return None

        if observation.mrp_paise == 0:
            return None

        discount = (observation.mrp_paise - observation.price_paise) / observation.mrp_paise

        if discount >= rule.threshold_pct:
            return RuleMatch(
                observation=observation,
                rule_id=rule.rule_id,
                rule_type="deal",
                channels=rule.channels,
                context={
                    "discount_pct": discount,
                    "threshold_pct": rule.threshold_pct,
                    "mrp": observation.mrp_paise / 100,
                    "price": observation.price_paise / 100,
                },
            )

        return None
