from __future__ import annotations

from commerce_platform.stock.run_support import redact_url


def test_redact_url_strips_query_length_hint() -> None:
    u = "https://www.example.com/path/to/page?token=secret&x=1"
    r = redact_url(u)
    assert "secret" not in r
    assert "example.com" in r
