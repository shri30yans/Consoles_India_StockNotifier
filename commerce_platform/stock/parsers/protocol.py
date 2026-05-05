"""Parser protocol — each retailer parser implements this interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ListingSnapshot:
    """Title / brand / image extracted from a retailer PDP when the parser supports it."""

    title: str | None = None
    brand: str | None = None
    image_url: str | None = None


@dataclass(frozen=True)
class ParseSignal:
    """Retail scrape outcome. Read listing fields via ``listing_title`` / ``listing_brand`` / ``listing_image_url``."""

    in_stock: bool
    price_inr: float | None = None
    mrp_inr: float | None = None
    method: str = ""
    offers: tuple[str, ...] = ()
    listing: ListingSnapshot | None = None

    @property
    def listing_title(self) -> str | None:
        return None if self.listing is None else self.listing.title

    @property
    def listing_brand(self) -> str | None:
        return None if self.listing is None else self.listing.brand

    @property
    def listing_image_url(self) -> str | None:
        return None if self.listing is None else self.listing.image_url


class Parser(Protocol):
    def parse(self, html: str, url: str) -> ParseSignal: ...
