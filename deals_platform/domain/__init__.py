"""Pure domain types and business rules. No I/O, no frameworks."""

from deals_platform.domain.events import (
    DealCandidate,
    EnrichedDeal,
    PublishablePost,
    ScoredDeal,
)
from deals_platform.domain.models import (
    Category,
    Money,
    Offer,
    PriceSnapshot,
    ProductRef,
    RetailerKey,
)

__all__ = [
    "Category",
    "DealCandidate",
    "EnrichedDeal",
    "Money",
    "Offer",
    "PriceSnapshot",
    "ProductRef",
    "PublishablePost",
    "RetailerKey",
    "ScoredDeal",
]
