#!/usr/bin/env python3
"""Print PA-API affiliate ``DetailPageURL`` values for one or more ASINs.

Requires ``AMAZON_PA_API_ACCESS_KEY``, ``AMAZON_PA_API_SECRET_KEY``, and
``AMAZON_AFFILIATE_TAG`` (and optionally ``AMAZON_PA_API_COUNTRY``, default ``IN``).

Example::

    python scripts/amazon_paapi_affiliate_links.py B0CY5QW186 B0FWJJCKCB

    python scripts/amazon_paapi_affiliate_links.py --json < asins.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Repo root on sys.path for ``commerce_platform``
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from amazon_paapi.errors import RequestError  # noqa: E402

from commerce_platform.platform.amazon_paapi import (  # noqa: E402
    AmazonPaapiAffiliateClient,
    load_amazon_paapi_settings,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve ASINs to Product Advertising API affiliate product URLs."
    )
    parser.add_argument(
        "asins",
        nargs="*",
        help="Product ASINs (space-separated). If omitted, read non-empty lines from stdin.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON array of {asin, title, detail_page_url}",
    )
    args = parser.parse_args()

    if args.asins:
        asins = list(args.asins)
    else:
        asins = [
            line.strip()
            for line in sys.stdin
            if line.strip() and not line.strip().startswith("#")
        ]

    if not asins:
        parser.error("Provide ASINs as arguments or on stdin.")

    try:
        settings = load_amazon_paapi_settings()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    client = AmazonPaapiAffiliateClient(settings)
    try:
        rows = client.affiliate_links_for_asins(asins)
    except RequestError as exc:
        print(f"PA-API error: {exc}", file=sys.stderr)
        print(
            "If Amazon returned AssociateNotEligible (403), your Associates account "
            "does not yet qualify for Product Advertising API access. "
            "Check Associates Central (Product Advertising API eligibility).",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "asin": r.asin,
                        "title": r.title,
                        "detail_page_url": r.detail_page_url,
                    }
                    for r in rows
                ],
                indent=2,
            )
        )
    else:
        for r in rows:
            label = r.title or r.asin or "?"
            url = r.detail_page_url or ""
            print(f"{label}\n  {url}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
