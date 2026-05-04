"""Unified listing metadata for stock signals (Amazon, Flipkart, wishlist)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ListingOrigin = Literal["amazon_product", "flipkart_product", "amazon_wishlist"]


@dataclass(frozen=True)
class StockListingSurface:
    """Name, canonical page URL, and scrape origin — shared by all stock sources."""

    display_name: str
    page_url: str
    origin: ListingOrigin
