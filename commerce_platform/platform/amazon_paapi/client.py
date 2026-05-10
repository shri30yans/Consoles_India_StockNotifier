"""Resolve ASINs to Product Advertising API ``DetailPageURL`` (affiliate-tagged) links."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from commerce_platform.platform.amazon_paapi.settings import AmazonPaapiSettings

# Third-party package emits a migration warning to Creators API; suppress at import.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from amazon_paapi import AmazonApi


@dataclass(frozen=True, slots=True)
class PaapiAffiliateItem:
    """One ASIN and the PA-API ``DetailPageURL`` for your PartnerTag (when returned)."""

    asin: str | None
    detail_page_url: str | None
    title: str | None


class AmazonPaapiAffiliateClient:
    """Thin wrapper around ``python-amazon-paapi`` for tagged product URLs."""

    def __init__(self, settings: AmazonPaapiSettings) -> None:
        self._settings = settings
        self._api = AmazonApi(
            settings.access_key,
            settings.secret_key,
            settings.partner_tag,
            settings.country,
            throttling=settings.throttling_seconds,
        )

    def affiliate_links_for_asins(self, asins: list[str]) -> list[PaapiAffiliateItem]:
        """Call ``GetItems`` and return ``DetailPageURL`` plus title for each item.

        ASINs are de-duplicated and requested in chunks of up to 10 (PA-API limit).
        Order follows the API response (not necessarily input order).
        """
        cleaned = [a.strip().upper() for a in asins if a and str(a).strip()]
        if not cleaned:
            return []

        items = self._api.get_items(cleaned)
        out: list[PaapiAffiliateItem] = []
        for item in items:
            title: str | None = None
            if item.item_info and item.item_info.title:
                title = item.item_info.title.display_value
            out.append(
                PaapiAffiliateItem(
                    asin=item.asin,
                    detail_page_url=item.detail_page_url,
                    title=title,
                )
            )
        return out
