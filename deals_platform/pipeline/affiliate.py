"""Affiliate URL builder. Strips foreign tags, appends ours.

Per-retailer rules live here so ingestion code stays clean.
"""

from __future__ import annotations

import os
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def _strip_params(url: str, drop: set[str]) -> str:
    parts = urlparse(url)
    kept = [(k, v) for k, v in parse_qsl(parts.query) if k.lower() not in drop]
    return urlunparse(parts._replace(query=urlencode(kept)))


def build_affiliate_url(retailer: str, url: str) -> str:
    if retailer == "amazon":
        tag = os.environ.get("AMAZON_AFFILIATE_TAG", "").strip()
        url = _strip_params(url, {"tag", "ref", "ref_", "smid"})
        if not tag:
            return url
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}tag={tag}"

    if retailer == "flipkart":
        affid = os.environ.get("FLIPKART_AFFILIATE_ID", "").strip()
        token = os.environ.get("FLIPKART_AFFILIATE_TOKEN", "").strip()
        url = _strip_params(url, {"affid", "affExtParam1", "affExtParam2"})
        if not affid:
            return url
        sep = "&" if "?" in url else "?"
        suffix = f"affid={affid}"
        if token:
            suffix += f"&affExtParam1={token}"
        return f"{url}{sep}{suffix}"

    return _strip_params(url, {"utm_source", "utm_medium", "utm_campaign"})


def is_affiliate_url(url: str) -> bool:
    return bool(re.search(r"[?&](tag|affid|aff_id)=", url))
