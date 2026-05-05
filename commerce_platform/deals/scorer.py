"""Deal scoring — compute deal quality scores from price history."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from commerce_platform.platform.config.schema import ScoringWeightsConfig
from commerce_platform.platform.store.repos import ConfigSettingsRepo, PriceRepo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DealScore:
    """Result of scoring a deal candidate."""

    score: float  # 0.0 – 1.0
    reasons: list[str]  # human-readable components
    discount_pct: float | None


class DealScorer:
    """Compute deal quality scores using historical price data + config weights."""

    def __init__(
        self,
        config_repo: ConfigSettingsRepo,
        price_repo: PriceRepo,
        default_weights: ScoringWeightsConfig,
    ) -> None:
        self._config_repo = config_repo
        self._price_repo = price_repo
        self._default_weights = default_weights

    async def score_listing(
        self,
        product_id: str | None,
        retailer: str,
        price_paise: int,
        mrp_paise: int | None,
    ) -> DealScore:
        """Score a deal candidate using price history + MRP discount."""
        weights = await self._load_weights()
        contributions: dict[str, float] = {}
        reasons: list[str] = []

        # Historical scoring (catalog products only)
        if product_id:
            try:
                min_90d = await self._price_repo.min_price(product_id, retailer=None, days=90)
                med_30d = await self._price_repo.median_price(product_id, retailer=None, days=30)
                xr_min = await self._price_repo.cross_retailer_min(product_id)

                # 90-day low: 1.0 if at/below low, scales linearly to 0.0 at 20% above
                if min_90d and min_90d > 0:
                    pct_above = max(0.0, (price_paise - min_90d) / min_90d)
                    score_90d = max(0.0, 1.0 - pct_above / 0.20)
                    contributions["lowest_90d"] = weights.lowest_90d * score_90d
                    if score_90d > 0.01:
                        reasons.append(f"90-day low: {score_90d:.0%}")

                # 30-day median: binary (below or not)
                if med_30d and price_paise < med_30d:
                    contributions["below_30d_median"] = weights.below_30d_median
                    reasons.append("Below 30-day median")

                # Cross-retailer best: binary
                if xr_min and price_paise <= xr_min:
                    contributions["cross_retailer_best"] = weights.cross_retailer_best
                    reasons.append("Best across retailers")
            except Exception:
                logger.exception("Failed to load price history for %s", product_id)

        # MRP discount (works for all products)
        discount_pct = None
        if mrp_paise and mrp_paise > 0:
            discount_pct = (mrp_paise - price_paise) / mrp_paise
            # Scale: 1.0 at 50% discount, 0.0 at 0% discount
            score_discount = min(1.0, discount_pct / 0.50)
            contributions["discount_vs_mrp"] = weights.discount_vs_mrp * score_discount
            if score_discount > 0.01:
                reasons.append(f"{discount_pct:.0%} off MRP")

        score = sum(contributions.values())
        return DealScore(round(score, 3), reasons, discount_pct)

    async def _load_weights(self) -> ScoringWeightsConfig:
        """Load weights from DB config, with fallback to defaults."""
        try:
            weights_dict = await self._config_repo.get_all_prefixed("deals.scoring.weights.")
            if weights_dict:
                return ScoringWeightsConfig(
                    lowest_90d=float(weights_dict.get("deals.scoring.weights.lowest_90d", self._default_weights.lowest_90d)),
                    below_30d_median=float(weights_dict.get("deals.scoring.weights.below_30d_median", self._default_weights.below_30d_median)),
                    discount_vs_mrp=float(weights_dict.get("deals.scoring.weights.discount_vs_mrp", self._default_weights.discount_vs_mrp)),
                    cross_retailer_best=float(weights_dict.get("deals.scoring.weights.cross_retailer_best", self._default_weights.cross_retailer_best)),
                    has_offers=float(weights_dict.get("deals.scoring.weights.has_offers", self._default_weights.has_offers)),
                    aggregator_corroborated=float(weights_dict.get("deals.scoring.weights.aggregator_corroborated", self._default_weights.aggregator_corroborated)),
                )
        except Exception:
            logger.exception("Failed to load weights from DB, using defaults")

        return self._default_weights
