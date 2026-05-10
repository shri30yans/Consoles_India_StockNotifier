"""Unit tests for PA-API affiliate client (mocked; no live Amazon calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from amazon_paapi.models import Country
from commerce_platform.platform.amazon_paapi.client import AmazonPaapiAffiliateClient
from commerce_platform.platform.amazon_paapi.settings import AmazonPaapiSettings


def test_affiliate_links_maps_items() -> None:
    settings = AmazonPaapiSettings(
        access_key="k",
        secret_key="s",
        partner_tag="mytag-21",
        country=Country.IN,
        throttling_seconds=0.0,
    )
    mock_item = MagicMock()
    mock_item.asin = "B0TEST1234"
    mock_item.detail_page_url = "https://www.amazon.in/dp/B0TEST1234?tag=mytag-21"
    mock_item.item_info.title.display_value = "Example Product"

    with patch("commerce_platform.platform.amazon_paapi.client.AmazonApi") as api_cls:
        api_cls.return_value.get_items.return_value = [mock_item]
        client = AmazonPaapiAffiliateClient(settings)
        out = client.affiliate_links_for_asins(["b0test1234"])

    assert len(out) == 1
    assert out[0].asin == "B0TEST1234"
    assert out[0].detail_page_url.endswith("tag=mytag-21")
    assert out[0].title == "Example Product"
