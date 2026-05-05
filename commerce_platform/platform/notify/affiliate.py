"""Affiliate link rewriting — append affiliate parameters to retailer URLs."""

from __future__ import annotations

import logging
import urllib.parse

from commerce_platform.platform.store.repos import ConfigSettingsRepo

logger = logging.getLogger(__name__)


class AffiliateRewriter:
    """Rewrites product URLs with affiliate parameters for monetization."""

    _PARAM_DEFAULTS = {
        "amazon": "tag",
        "flipkart": "affid",
        "ajio": "utm_source",
        "myntra": "utm_source",
    }

    def __init__(self, config_repo: ConfigSettingsRepo) -> None:
        self._config_repo = config_repo
        self._cache: dict[str, tuple[str, str] | None] = {}

    async def rewrite(self, url: str | None, retailer: str) -> str | None:
        """Rewrite URL with affiliate tag. Returns original URL if no tag configured."""
        if not url:
            return None

        # Check cache first
        cache_key = f"{retailer}"
        if cache_key in self._cache:
            tag_info = self._cache[cache_key]
            if tag_info is None:
                return url
            param, tag = tag_info
        else:
            # Fetch from config
            tag = await self._config_repo.get(f"affiliate.{retailer}.tag")
            if not tag:
                self._cache[cache_key] = None
                return url

            param = await self._config_repo.get(
                f"affiliate.{retailer}.param",
                self._PARAM_DEFAULTS.get(retailer, "ref"),
            )
            self._cache[cache_key] = (param, tag)

        # Rewrite URL
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        qs[param] = [tag]
        new_query = urllib.parse.urlencode(qs, doseq=True)
        return parsed._replace(query=new_query).geturl()

    def cache_invalidate(self, retailer: str | None = None) -> None:
        """Clear cache for a retailer or all retailers."""
        if retailer:
            self._cache.pop(f"{retailer}", None)
        else:
            self._cache.clear()
