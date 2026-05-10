from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from commerce_platform.stock.listing_preview import scrape_listing


def _require_live_slt_enabled() -> None:
    if os.getenv("RUN_LIVE_SLT", "").strip() != "1":
        pytest.skip("Live SLT disabled. Set RUN_LIVE_SLT=1 to run live AJIO scrape tests.")


def _live_ajio_url() -> str:
    return os.getenv(
        "LIVE_AJIO_URL",
        "https://www.ajio.com/p/469955188_white",
    ).strip()


def test_slt_ajio_listing_scrape_flow_live() -> None:
    _require_live_slt_enabled()
    config_path = Path(__file__).resolve().parents[1] / "config.yaml"
    url = _live_ajio_url()

    result = asyncio.run(
        scrape_listing(
            url,
            config_path=config_path,
            label="slt_ajio_live",
        )
    )

    assert result.retailer == "ajio"
    assert result.ok, f"Live AJIO scrape failed: reason={result.reason!r} fetch_url={result.fetch_url!r}"
    assert (
        result.name is not None
        or result.brand is not None
        or result.image_url is not None
        or result.price_inr is not None
    ), "Live AJIO scrape returned no useful fields"
