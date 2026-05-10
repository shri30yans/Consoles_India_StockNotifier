"""Unit tests for Twitter plain-text formatting (no API calls)."""

from commerce_platform.platform.notify.twitter import markdown_to_plain_x


def test_markdown_to_plain_strips_bold_and_links() -> None:
    md = "**PS5**: in stock\n**Price:** ₹50,000\n[View](https://amazon.in/dp/X)"
    plain = markdown_to_plain_x(md, max_len=500)
    assert "**" not in plain
    assert "[View]" not in plain
    assert "https://amazon.in/dp/X" in plain


def test_markdown_to_plain_truncates() -> None:
    long = "x" * 400
    plain = markdown_to_plain_x(long, max_len=50)
    assert len(plain) <= 50
    assert plain.endswith("…")
