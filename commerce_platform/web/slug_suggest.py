"""Derive a catalog product_id suggestion from a human-readable title."""

from __future__ import annotations

import re

from commerce_platform.platform.product_name import coerce_product_name


def suggest_product_id_from_title(title: str, *, max_len: int = 64) -> str:
    """Lowercase slug: letters, digits, underscores; fits ``slug_ok``."""
    name = coerce_product_name(title)
    name = re.sub(r"\s*:\s*Amazon\.in.*$", "", name, flags=re.IGNORECASE).strip()
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        return "product"
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("_")
    return slug or "product"
