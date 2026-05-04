"""Map (retailer, source_type) to listing origin without string hacks."""

from __future__ import annotations

from commerce_platform.platform.events.listing_surface import ListingOrigin

_ORIGIN_MAP = {
    ("amazon", "product"): "amazon_product",
    ("amazon", "wishlist"): "amazon_wishlist",
    ("flipkart", "product"): "flipkart_product",
}


def get_origin(retailer: str, source_type: str) -> ListingOrigin:
    """
    Resolve the listing origin from retailer and source type.

    Args:
        retailer: "amazon", "flipkart", etc.
        source_type: "product", "wishlist", etc.

    Returns:
        ListingOrigin: "amazon_product", "flipkart_product", "amazon_wishlist"

    Raises:
        ValueError: If the combination is not recognized.
    """
    origin = _ORIGIN_MAP.get((retailer, source_type))
    if origin is None:
        raise ValueError(f"Unknown origin: retailer={retailer}, source_type={source_type}")
    return origin  # type: ignore
