"""Stable wishlist list key for product_id + alert routing."""

from __future__ import annotations

import hashlib

from commerce_platform.platform.config.schema import PlatformSourceConfig


def _slug_ok(v: str) -> bool:
    return bool(v) and v.replace("_", "").replace("-", "").isalnum()


def resolve_wishlist_list_key(source: PlatformSourceConfig) -> str:
    """Return a stable key for this wishlist source (used in product_id wishlist:{key}:{asin})."""
    if source.type != "amazon_wishlist":
        raise ValueError("resolve_wishlist_list_key only for amazon_wishlist sources")
    uid = (source.wishlist_id or "").strip().lower()
    if uid:
        if not _slug_ok(uid):
            raise ValueError(
                f"wishlist_id must be alphanumeric with optional _ or -: {source.wishlist_id!r}"
            )
        return uid
    url = (source.url or "").strip()
    if not url:
        return "unknown"
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"wl_{h}"
