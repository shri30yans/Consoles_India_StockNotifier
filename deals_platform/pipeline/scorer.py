"""Deterministic, transparent deal scorer.

Each signal returns a number in [0, 1] and a contribution weight. The composite
score is a weighted sum, clamped to [0, 1]. The breakdown is preserved so the
LLM and audit log can show *why* a deal scored high.
"""

from __future__ import annotations

from dataclasses import dataclass

from deals_platform.domain.events import EnrichedDeal, ScoreBreakdown, ScoredDeal


@dataclass(frozen=True)
class ScoringWeights:
    lowest_in_90d: float = 0.35
    below_30d_median: float = 0.25
    discount_vs_mrp: float = 0.10
    cross_retailer_best: float = 0.15
    has_offers: float = 0.05
    aggregator_corroborated: float = 0.10


class CompositeScorer:
    def __init__(
        self,
        weights: ScoringWeights | None = None,
        *,
        threshold: float = 0.55,
        # discount % vs 30-day median needed to count as a strong deal
        median_discount_target: float = 0.15,
        # discount % vs MRP needed to score full marks
        mrp_discount_target: float = 0.30,
    ) -> None:
        self._w = weights or ScoringWeights()
        self.threshold = threshold
        self._median_target = median_discount_target
        self._mrp_target = mrp_discount_target

    def score(self, deal: EnrichedDeal) -> ScoredDeal:
        signals: dict[str, float] = {}
        reasons: list[str] = []
        price = deal.snapshot.price

        # --- lowest in 90 days ---
        if deal.history_min_90d is not None:
            if price.minor_units <= deal.history_min_90d.minor_units:
                signals["lowest_in_90d"] = 1.0
                reasons.append(f"Lowest price in 90 days ({price})")
            else:
                # partial credit if within 5% of the 90-day low
                ratio = deal.history_min_90d.minor_units / price.minor_units
                signals["lowest_in_90d"] = max(0.0, ratio - 0.95) * 20.0  # 0..1
        else:
            signals["lowest_in_90d"] = 0.0

        # --- below 30-day median (deal vs typical price) ---
        if deal.history_median_30d is not None and deal.history_median_30d.minor_units > 0:
            drop = 1.0 - price.minor_units / deal.history_median_30d.minor_units
            score = max(0.0, min(1.0, drop / self._median_target))
            signals["below_30d_median"] = score
            if drop >= self._median_target:
                reasons.append(
                    f"{drop * 100:.0f}% below 30-day median ({deal.history_median_30d})"
                )
        else:
            signals["below_30d_median"] = 0.0

        # --- discount vs MRP (penalize fake MRP by capping influence) ---
        d = deal.snapshot.discount_pct_vs_mrp
        if d is not None:
            normalized = max(0.0, min(1.0, (d / 100.0) / self._mrp_target))
            signals["discount_vs_mrp"] = normalized
            if d >= 30:
                reasons.append(f"{d:.0f}% off MRP")
        else:
            signals["discount_vs_mrp"] = 0.0

        # --- cross-retailer: are we the cheapest right now? ---
        if deal.cross_retailer_min is not None:
            if price.minor_units <= deal.cross_retailer_min.minor_units:
                signals["cross_retailer_best"] = 1.0
                reasons.append("Cheapest across tracked retailers")
            else:
                ratio = deal.cross_retailer_min.minor_units / price.minor_units
                signals["cross_retailer_best"] = max(0.0, ratio - 0.9) * 10.0
        else:
            signals["cross_retailer_best"] = 0.0

        # --- offers stack ---
        signals["has_offers"] = 1.0 if deal.offers else 0.0
        if deal.offers:
            reasons.append(f"{len(deal.offers)} additional offer(s) available")

        # --- aggregator corroboration: someone else flagged this too ---
        agg = deal.candidate.source.startswith("aggregator:")
        signals["aggregator_corroborated"] = 1.0 if agg else 0.0

        # weighted sum
        total = (
            signals["lowest_in_90d"] * self._w.lowest_in_90d
            + signals["below_30d_median"] * self._w.below_30d_median
            + signals["discount_vs_mrp"] * self._w.discount_vs_mrp
            + signals["cross_retailer_best"] * self._w.cross_retailer_best
            + signals["has_offers"] * self._w.has_offers
            + signals["aggregator_corroborated"] * self._w.aggregator_corroborated
        )
        total = max(0.0, min(1.0, total))

        return ScoredDeal(
            deal=deal,
            breakdown=ScoreBreakdown(
                score=total,
                signals=dict(signals),
                reasons=tuple(reasons),
            ),
        )
