"""Money parsing helpers shared across retailer parsers."""

from __future__ import annotations

import re

_RUPEE_RE = re.compile(r"[\u20b9\s,]")  # ₹, whitespace, commas


def rupee_to_float(text: str | None) -> float | None:
    """Parse a ₹-prefixed/decorated price string to float rupees.

    Returns None on parse failure. Handles ``₹1,49,990``, ``Rs. 1499``, etc.
    """
    if text is None:
        return None
    cleaned = _RUPEE_RE.sub("", text).replace("Rs.", "").replace("Rs", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None
