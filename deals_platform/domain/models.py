"""Value objects shared across all layers. Frozen, hashable, no I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

RetailerKey = str  # "amazon" | "flipkart" | "croma" | "myntra" | ...


class Category(str, Enum):
    TECH = "tech"
    GAMING = "gaming"
    LIFESTYLE = "lifestyle"
    HOME = "home"
    BEAUTY = "beauty"
    BABY = "baby"
    GROCERY = "grocery"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Money:
    """Integer paise to avoid float drift. ₹1,299.00 -> Money(129900, 'INR')."""

    minor_units: int
    currency: str = "INR"

    @classmethod
    def from_rupees(cls, rupees: float, currency: str = "INR") -> Money:
        return cls(int(round(rupees * 100)), currency)

    @property
    def rupees(self) -> float:
        return self.minor_units / 100.0

    def __str__(self) -> str:
        symbol = "₹" if self.currency == "INR" else self.currency + " "
        return f"{symbol}{self.rupees:,.0f}"


@dataclass(frozen=True)
class Offer:
    """Bank/card/coupon offer that stacks on top of price."""

    description: str
    flat_off: Money | None = None
    percent_off: float | None = None
    code: str | None = None


@dataclass(frozen=True)
class ProductRef:
    """Canonical product identity across retailers.

    `canonical_id` is computed by the normalizer (e.g. brand+model hash);
    `retailer_sku` is the per-retailer id (ASIN, FSN, SKU).
    """

    canonical_id: str
    retailer: RetailerKey
    retailer_sku: str
    title: str
    brand: str | None = None
    image_url: str | None = None
    product_url: str = ""


@dataclass(frozen=True)
class PriceSnapshot:
    """One point in time-series price history."""

    product_canonical_id: str
    retailer: RetailerKey
    price: Money
    mrp: Money | None
    in_stock: bool
    rating: float | None
    rating_count: int | None
    offers: tuple[Offer, ...] = field(default_factory=tuple)
    captured_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @property
    def discount_pct_vs_mrp(self) -> float | None:
        if self.mrp is None or self.mrp.minor_units <= 0:
            return None
        return 100.0 * (1.0 - self.price.minor_units / self.mrp.minor_units)
