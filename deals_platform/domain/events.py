"""Events that flow through the pipeline. Each layer consumes one and produces the next."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from deals_platform.domain.models import Category, Money, Offer, PriceSnapshot, RetailerKey


@dataclass(frozen=True)
class DealCandidate:
    """Raw signal from a Source. Minimal — the Normalizer fills the rest."""

    source: str  # "scraper:amazon" | "aggregator:desidime" | "aggregator:reddit" | ...
    retailer: RetailerKey
    product_url: str
    title: str | None = None
    observed_price: Money | None = None
    observed_mrp: Money | None = None
    raw_payload: dict = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def fingerprint(self) -> str:
        """Idempotency key for dedupe (per-day per-URL)."""
        day = self.discovered_at.strftime("%Y%m%d")
        return f"{self.retailer}|{self.product_url}|{day}"


@dataclass(frozen=True)
class EnrichedDeal:
    """Candidate after canonicalization, history lookup, and offer enrichment."""

    candidate: DealCandidate
    canonical_id: str
    title: str
    brand: str | None
    image_url: str | None
    snapshot: PriceSnapshot
    history_min_90d: Money | None
    history_median_30d: Money | None
    cross_retailer_min: Money | None  # cheapest across all retailers right now
    offers: tuple[Offer, ...] = field(default_factory=tuple)

    @property
    def is_lowest_in_90d(self) -> bool:
        return (
            self.history_min_90d is not None
            and self.snapshot.price.minor_units <= self.history_min_90d.minor_units
        )


@dataclass(frozen=True)
class ScoreBreakdown:
    """Transparent reasoning — also used for LLM context and audit logs."""

    score: float
    signals: dict[str, float]  # signal_name -> contribution
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ScoredDeal:
    deal: EnrichedDeal
    breakdown: ScoreBreakdown


@dataclass(frozen=True)
class PublishablePost:
    """Output of the curation agent — ready for distribution."""

    scored: ScoredDeal
    category: Category
    target_channels: tuple[str, ...]  # channel keys from channels.yaml
    title: str
    body_markdown: str
    affiliate_url: str
    image_url: str | None = None
