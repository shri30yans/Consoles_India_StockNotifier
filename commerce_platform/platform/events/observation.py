"""Unified price/stock observation — single event type for all sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class PriceObservation:
    """A single price/stock observation from any source (scraper, wishlist, aggregator)."""

    product_id: str  # Internal product ID (from catalog, or None if unknown)
    retailer: str  # "amazon", "flipkart", "myntra"
    price_paise: int  # Actual price in paise (0 if unknown)
    mrp_paise: int | None  # MRP/list price
    in_stock: bool  # Current stock status
    source: str  # "scraper:amazon", "wishlist:amazon", "aggregator:desidime"
    observed_at: str  # ISO timestamp when scraped
    product_url: str | None = None  # Link to product page
    product_title: str | None = None  # "PS5 Console"
    offers: list[str] = field(default_factory=list)  # Special offers/codes
    raw_payload: dict = field(default_factory=dict)  # Store raw HTML/JSON for audit
    context: dict = field(default_factory=dict)  # Source metadata: deal_score, reddit_score, etc.

    def __post_init__(self) -> None:
        """Validate observation."""
        if self.price_paise < 0:
            raise ValueError(f"price_paise must be non-negative: {self.price_paise}")
        if self.mrp_paise is not None and self.mrp_paise < 0:
            raise ValueError(f"mrp_paise must be non-negative: {self.mrp_paise}")


@dataclass(frozen=True)
class RuleMatch:
    """A rule matched an observation."""

    observation: PriceObservation
    rule_id: str  # "ps5_back_in_stock", "ps5_30pct_off", "ps5_below_50k"
    rule_type: str  # "stock", "price_below", "discount_pct"
    channels: list[str]  # Target notification channels
    context: dict = field(default_factory=dict)  # {threshold, prev_price, discount, etc}
    matched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def discount_percent(self) -> float:
        """Calculate discount % if mrp available."""
        if self.observation.mrp_paise and self.observation.mrp_paise > 0:
            return (
                (self.observation.mrp_paise - self.observation.price_paise)
                / self.observation.mrp_paise
            )
        return 0.0

    def price_rupees(self) -> float:
        """Current price in rupees."""
        return self.observation.price_paise / 100


@dataclass(frozen=True)
class Notification:
    """A notification to send to channels."""

    product_id: str
    rule_id: str
    rule_type: str  # "stock", "price", "deal"
    title: str  # "PS5 Back in Stock" or "PS5: ₹45k (30% off)"
    body: str  # Markdown formatted
    target_channels: list[str]
    retailer: str
    price_rupees: float | None = None
    discount_pct: float | None = None
    in_stock: bool | None = None
    product_url: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
