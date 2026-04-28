from __future__ import annotations

import logging
import random
from collections.abc import Iterable

from stock_notifier.fetch.default_headers import DEFAULT_REQUEST_HEADERS
from stock_notifier.models import AppConfig

logger = logging.getLogger(__name__)

_ua_instance = None

PLAYWRIGHT_FALLBACK_UA: list[str] = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
]


def _user_agent_singleton():
    global _ua_instance
    if _ua_instance is None:
        from fake_useragent import UserAgent

        _ua_instance = UserAgent()
    return _ua_instance


def random_user_agent_string() -> str:
    """Return a plausible browser User-Agent, with safe fallback."""
    try:
        ua = _user_agent_singleton()
        s = ua.random
        if isinstance(s, str) and s.strip():
            return s.strip()
    except Exception as e:
        logger.debug("fake-useragent failed: %s", e)
    h = random.choice(DEFAULT_REQUEST_HEADERS)
    return h["User-Agent"]


def _strip_user_agent_keys(headers: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() != "user-agent"}


def build_request_headers(
    app: AppConfig,
    headers_pool: Iterable[dict[str, str]] | None,
) -> dict[str, str]:
    """
    Merge retailer YAML header bundles with optional fake-useragent rotation.

    When ``use_fake_useragent`` is true, the ``User-Agent`` (any casing) from
    the chosen bundle is replaced with a freshly sampled UA. When the pool is
    empty, a minimal UA-only dict is used (still rotated when fake UA is on).
    """
    pool = list(headers_pool) if headers_pool else []
    if not pool:
        if app.use_fake_useragent:
            return {"User-Agent": random_user_agent_string()}
        return dict(random.choice(DEFAULT_REQUEST_HEADERS))

    base = {str(k): str(v) for k, v in dict(random.choice(pool)).items()}
    if not app.use_fake_useragent:
        return base

    merged = _strip_user_agent_keys(base)
    merged["User-Agent"] = random_user_agent_string()
    return merged


def playwright_extra_headers(
    app: AppConfig,
    headers_pool: Iterable[dict[str, str]] | None,
) -> dict[str, str]:
    """Headers passed to ``Page.set_extra_http_headers`` before navigation."""
    return build_request_headers(app, headers_pool)


def default_browser_user_agent(app: AppConfig) -> str:
    """Default UA for ``browser.new_context``."""
    if app.use_fake_useragent:
        return random_user_agent_string()
    return random.choice(PLAYWRIGHT_FALLBACK_UA)
