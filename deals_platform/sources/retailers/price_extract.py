"""Price/title extraction for the deals platform.

Lightweight parsers focused on price (not stock). Per-retailer extractors are
small and pluggable. Production-grade selectors live next to existing
`stock_notifier.parsers`; here we keep platform-specific extraction concerns.
"""

from __future__ import annotations

import logging
import re
from typing import Callable

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PriceTuple = tuple[str | None, float | None, float | None]  # (title, price, mrp)
Extractor = Callable[[BeautifulSoup], PriceTuple]


def _to_float(text: str | None) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _amazon(soup: BeautifulSoup) -> PriceTuple:
    title_el = soup.select_one("#productTitle")
    title = title_el.get_text(strip=True) if title_el else None

    price_el = soup.select_one(".a-price.a-text-price[data-a-strike] .a-offscreen")
    mrp = _to_float(price_el.get_text() if price_el else None)

    cur_el = soup.select_one("#corePriceDisplay_desktop_feature_div .a-price .a-offscreen")
    if not cur_el:
        cur_el = soup.select_one(".a-price .a-offscreen")
    price = _to_float(cur_el.get_text() if cur_el else None)
    return title, price, mrp


def _flipkart(soup: BeautifulSoup) -> PriceTuple:
    title_el = soup.select_one("h1 span.B_NuCI, span.VU-ZEz, h1")
    title = title_el.get_text(strip=True) if title_el else None

    price_el = soup.select_one("div._30jeq3._16Jk6d, div.Nx9bqj.CxhGGd")
    price = _to_float(price_el.get_text() if price_el else None)

    mrp_el = soup.select_one("div._3I9_wc._2p6lqe, div.yRaY8j")
    mrp = _to_float(mrp_el.get_text() if mrp_el else None)
    return title, price, mrp


def _croma(soup: BeautifulSoup) -> PriceTuple:
    title_el = soup.select_one("h1.pd-title, h1")
    title = title_el.get_text(strip=True) if title_el else None
    price_el = soup.select_one("span.amount, .pdp-price .amount")
    price = _to_float(price_el.get_text() if price_el else None)
    mrp_el = soup.select_one("span.old-price, .cr-old-price")
    mrp = _to_float(mrp_el.get_text() if mrp_el else None)
    return title, price, mrp


def _myntra(soup: BeautifulSoup) -> PriceTuple:
    # Myntra is JS-heavy; needs Playwright. Selectors are best-effort.
    title_el = soup.select_one("h1.pdp-title, h1.pdp-name")
    title = title_el.get_text(strip=True) if title_el else None
    price_el = soup.select_one("span.pdp-price strong, .pdp-price")
    price = _to_float(price_el.get_text() if price_el else None)
    mrp_el = soup.select_one("span.pdp-mrp s, .pdp-mrp")
    mrp = _to_float(mrp_el.get_text() if mrp_el else None)
    return title, price, mrp


_EXTRACTORS: dict[str, Extractor] = {
    "amazon": _amazon,
    "flipkart": _flipkart,
    "croma": _croma,
    "myntra": _myntra,
}


def extract_price_signal(html: str, retailer: str, url: str) -> PriceTuple | None:
    extractor = _EXTRACTORS.get(retailer)
    if extractor is None:
        logger.debug("no price extractor for retailer=%s", retailer)
        return None
    try:
        soup = BeautifulSoup(html, "lxml")
        return extractor(soup)
    except Exception:
        logger.exception("extractor crashed for %s %s", retailer, url)
        return None
