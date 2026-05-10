#!/usr/bin/env python3
"""Print PA-API request targets and Amazon's raw error JSON (no secrets)."""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from amazon_paapi import AmazonApi
    from amazon_paapi.helpers.requests import get_items_request
    from amazon_paapi.sdk.rest import ApiException

from commerce_platform.platform.amazon_paapi.settings import (
    load_amazon_paapi_settings,  # noqa: E402
)


def _mask(s: str, show: int = 4) -> str:
    if len(s) <= show * 2:
        return "***"
    return f"{s[:show]}...{s[-show:]}"


def main() -> int:
    settings = load_amazon_paapi_settings()
    api = AmazonApi(
        settings.access_key,
        settings.secret_key,
        settings.partner_tag,
        settings.country,
        throttling=0,
    )

    host = getattr(api, "_host", "webservices.amazon." + settings.country.lower())
    print("=== Values sent to Product Advertising API (GetItems) ===")
    print(f"  Country (library):     {settings.country!r}")
    print(f"  Marketplace string:    {api.marketplace}")
    print(f"  API host:              {host}")
    print(f"  Signing region:        {api.region}")
    print(f"  PartnerTag:            {settings.partner_tag!r}")
    print("  Partner type:          ASSOCIATES (fixed by library)")
    print(f"  Access Key (masked):   {_mask(settings.access_key)}")
    print()

    request = get_items_request(api, ["B0CY5QW186"])
    print("=== Sample GetItems request fields (from library) ===")
    print(f"  partner_tag on request: {request.partner_tag!r}")
    print(f"  marketplace:            {request.marketplace!r}")
    print(f"  item_ids:               {request.item_ids}")
    print()

    print("=== Live call ===")
    try:
        response = api.api.get_items(request)
        ok = response.items_result is not None and response.items_result.items
        print(f"  Success: {bool(ok)}")
        if ok:
            for it in response.items_result.items[:1]:
                print(f"  ASIN: {it.asin}")
                print(f"  DetailPageURL: {it.detail_page_url[:80]}…")
        return 0
    except ApiException as exc:
        print(f"  HTTP status: {exc.status}")
        body = getattr(exc, "body", None) or ""
        print("  Raw response body:")
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print(f"  {body}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
