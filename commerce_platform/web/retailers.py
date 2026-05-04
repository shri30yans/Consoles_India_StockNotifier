"""Parse retailer listing URLs for user requests and overlay creation."""

from __future__ import annotations

import re
from urllib.parse import urlparse

# Registrable site suffixes (no www — hosts are matched canonically).
_RETAIL_SITE_SUFFIXES = frozenset({"amazon.in", "flipkart.com", "ajio.com"})


def _canonical_retail_suffix(netloc: str) -> str | None:
    """Return the known retail suffix for this host, or None.

    Accepts apex and subdomains: ``www.ajio.com``, ``ajio.com``, ``m.flipkart.com``
    all map to ``ajio.com`` / ``flipkart.com``.
    """
    host = (netloc or "").lower().split(":", 1)[0]
    for suffix in _RETAIL_SITE_SUFFIXES:
        if host == suffix or host.endswith("." + suffix):
            return suffix
    return None


def validate_public_product_url(url: str) -> tuple[bool, str | None]:
    u = url.strip()
    if not u.startswith("https://"):
        return False, "Only https:// URLs are allowed"
    try:
        parsed = urlparse(u)
    except Exception:
        return False, "Invalid URL"
    if _canonical_retail_suffix(parsed.netloc or "") is None:
        return False, "Only Amazon India, Flipkart, and AJIO URLs are supported"
    return True, None


def detect_retailer_and_asin(url: str) -> tuple[str | None, str | None]:
    """Return (retailer_key, sku_or_none). Amazon uses ASIN; others use site-specific ids when present."""
    ok, err = validate_public_product_url(url)
    if not ok:
        return None, None
    host = urlparse(url).netloc.lower()
    site = _canonical_retail_suffix(host)
    if site == "amazon.in":
        m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url, re.I)
        asin = m.group(1).upper() if m else None
        return "amazon", asin
    if site == "flipkart.com":
        return "flipkart", None
    if site == "ajio.com":
        m = re.search(r"/p/([^/?#]+)", url, re.I)
        sku = m.group(1) if m else None
        return "ajio", sku
    return None, None
