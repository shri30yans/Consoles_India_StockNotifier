from __future__ import annotations

from stock_notifier.models import ParseContext, ParseResult
from stock_notifier.parsers import amazon as amazon_parser
from stock_notifier.parsers import flipkart as flipkart_parser
from stock_notifier.retailers import PARSER_SUPPORTED_WEBSITE_KEYS


def parse_html(html: str, ctx: ParseContext) -> ParseResult:
    """
    Pure dispatch to retailer parsers.
    Callers must ensure `ctx.website_key` is in PARSER_SUPPORTED_WEBSITE_KEYS
    (enforced when loading `jobs.yaml`).
    """
    site = ctx.website_key
    if site not in PARSER_SUPPORTED_WEBSITE_KEYS:
        raise RuntimeError(
            f"Parser dispatch bug: {site!r} is not a supported retailer "
            f"(supported: {sorted(PARSER_SUPPORTED_WEBSITE_KEYS)})",
        )
    if site == "amazon":
        return amazon_parser.parse(html, ctx)
    if site == "flipkart":
        return flipkart_parser.parse(html, ctx)
    raise RuntimeError(f"Unhandled supported site: {site}")
