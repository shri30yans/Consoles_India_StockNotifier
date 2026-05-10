"""Load Product Advertising API credentials and marketplace from the environment."""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from amazon_paapi.models import Country, CountryCode


@dataclass(frozen=True, slots=True)
class AmazonPaapiSettings:
    """PA-API 5 credentials and target marketplace (see Amazon locale / host table)."""

    access_key: str
    secret_key: str
    partner_tag: str
    country: CountryCode
    throttling_seconds: float = 1.0


def load_amazon_paapi_settings() -> AmazonPaapiSettings:
    """Read ``AMAZON_PA_API_*`` and ``AMAZON_AFFILIATE_TAG`` from the environment.

    Required:
    - ``AMAZON_PA_API_ACCESS_KEY`` — access key from Associates / PA-API registration
    - ``AMAZON_PA_API_SECRET_KEY`` — secret key
    - ``AMAZON_AFFILIATE_TAG`` — store / tracking id (PartnerTag) for the target marketplace

    Optional:
    - ``AMAZON_PA_API_COUNTRY`` — two-letter marketplace code (default: ``IN`` for Amazon.in)
    - ``AMAZON_PA_API_THROTTLING`` — minimum seconds between PA-API calls (default: ``1``)
    """
    access = os.environ.get("AMAZON_PA_API_ACCESS_KEY", "").strip()
    secret = os.environ.get("AMAZON_PA_API_SECRET_KEY", "").strip()
    tag = os.environ.get("AMAZON_AFFILIATE_TAG", "").strip()
    if not access or not secret or not tag:
        raise RuntimeError(
            "Set AMAZON_PA_API_ACCESS_KEY, AMAZON_PA_API_SECRET_KEY, and "
            "AMAZON_AFFILIATE_TAG to use Product Advertising API."
        )

    raw_country = os.environ.get("AMAZON_PA_API_COUNTRY", "IN").strip().upper()
    if not hasattr(Country, raw_country):
        raise RuntimeError(
            f"Unsupported AMAZON_PA_API_COUNTRY={raw_country!r}. "
            f"Use one of: {', '.join(sorted(c for c in dir(Country) if c.isupper()))}"
        )
    country: CountryCode = getattr(Country, raw_country)

    throttle_raw = os.environ.get("AMAZON_PA_API_THROTTLING", "1").strip()
    try:
        throttling = float(throttle_raw)
    except ValueError as exc:
        raise RuntimeError(
            f"AMAZON_PA_API_THROTTLING must be a number, got {throttle_raw!r}"
        ) from exc
    if throttling < 0:
        raise RuntimeError("AMAZON_PA_API_THROTTLING must be >= 0")

    return AmazonPaapiSettings(
        access_key=access,
        secret_key=secret,
        partner_tag=tag,
        country=country,
        throttling_seconds=throttling,
    )
