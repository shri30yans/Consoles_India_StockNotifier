from __future__ import annotations

import pytest
from commerce_platform.adapters.fetch.http_headers import build_request_headers
from commerce_platform.stock.models import AppConfig


def _minimal_app(**kwargs) -> AppConfig:
    base = dict(
        notify=True,
        mode="requests",
        amazon_affiliate_tag="",
        telegram_chat_id="",
        logs_dir="logs",
        log_json=False,
        log_max_bytes=1024,
        log_backup_count=1,
        jitter_max_seconds=0.0,
        max_concurrent_per_transport=0,
        use_fake_useragent=True,
        http_client="aiohttp",
        curl_impersonate="chrome124",
        playwright_apply_stealth=True,
        playwright_locale="en-IN",
        playwright_timezone_id="Asia/Kolkata",
    )
    base.update(kwargs)
    return AppConfig(**base)


def test_build_headers_replaces_ua_when_fake_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _minimal_app(use_fake_useragent=True)
    monkeypatch.setattr(
        "commerce_platform.adapters.fetch.http_headers.random_user_agent_string",
        lambda: "SyntheticUA/1.0",
    )
    h = build_request_headers(app, [{"User-Agent": "OldUA", "X-Test": "1"}])
    assert h["User-Agent"] == "SyntheticUA/1.0"
    assert h["X-Test"] == "1"


def test_build_headers_keeps_bundle_when_fake_disabled() -> None:
    app = _minimal_app(use_fake_useragent=False)
    h = build_request_headers(app, [{"User-Agent": "KeepMe", "X-Test": "2"}])
    assert h["User-Agent"] == "KeepMe"
