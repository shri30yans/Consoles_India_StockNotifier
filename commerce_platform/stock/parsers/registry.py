"""Canonical parser registry for retailer product pages."""

from __future__ import annotations

from typing import Callable

from commerce_platform.stock.parsers import ajio as ajio_parser
from commerce_platform.stock.parsers import amazon as amazon_parser
from commerce_platform.stock.parsers import flipkart as flipkart_parser
from commerce_platform.stock.parsers.protocol import ParseSignal

RetailerParser = Callable[[str, str], ParseSignal]

_PARSERS: dict[str, RetailerParser] = {
    "amazon": amazon_parser.parse,
    "flipkart": flipkart_parser.parse,
    "ajio": ajio_parser.parse,
}


def parser_key_for_source(source: str) -> str:
    """Map watch.source (e.g. ``ajio_playwright``) to registry key."""
    if source.endswith("_playwright"):
        return source[: -len("_playwright")]
    return source


def get_parser_for_source(source: str) -> RetailerParser:
    key = parser_key_for_source(source)
    parser = _PARSERS.get(key)
    if parser is None:
        raise ValueError(f"No parser registered for source: {source} (normalized: {key})")
    return parser

