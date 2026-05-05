"""AJIO product page parser — price/stock from JSON-LD and light DOM fallbacks.

AJIO pages are JS-heavy; prefer ``source: ajio_playwright`` in config if aiohttp HTML
is missing price/stock. Selectors break when the site redesigns — re-scrape a saved
HTML sample and adjust ``_dom_price`` / stock heuristics as needed."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from commerce_platform.platform.product_name import coerce_product_name
from commerce_platform.stock.parsers.json_ld_brand import brand_from_json_ld_object
from commerce_platform.stock.parsers.protocol import ListingSnapshot, ParseSignal

logger = logging.getLogger(__name__)


def parse(page_html: str, url: str) -> ParseSignal:
    soup = BeautifulSoup(str(page_html), "html.parser")
    listing = _ajio_listing_snapshot(soup)

    ld = _parse_json_ld_product(soup)
    if ld is not None:
        price, mrp, in_stock, method = ld
        return ParseSignal(in_stock=in_stock, price_inr=price, mrp_inr=mrp, method=method, listing=listing)

    dom = _dom_fallback(soup)
    if dom is not None:
        return dom if listing is None else ParseSignal(
            in_stock=dom.in_stock,
            price_inr=dom.price_inr,
            mrp_inr=dom.mrp_inr,
            method=dom.method,
            offers=dom.offers,
            listing=listing,
        )

    logger.warning("AJIO parse: no JSON-LD Product and no DOM fallback matched url=%s", url[:80])
    return ParseSignal(in_stock=False, method="ajio_no_signals", listing=listing)


def _ajio_listing_snapshot(soup: BeautifulSoup) -> ListingSnapshot | None:
    title = _ajio_title(soup)
    brand = _ajio_brand(soup)
    image_url = _ajio_image(soup)

    if title:
        title = coerce_product_name(title).strip() or None
    if brand:
        brand = coerce_product_name(brand).strip() or None

    if not title and not brand and not image_url:
        return None
    return ListingSnapshot(title=title, brand=brand, image_url=image_url)


def _meta_content(soup: BeautifulSoup, *, prop: str | None = None, name: str | None = None) -> str | None:
    if prop:
        meta = soup.find("meta", attrs={"property": prop})
    elif name:
        meta = soup.find("meta", attrs={"name": name})
    else:
        return None
    if not meta:
        return None
    content = meta.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None


def _ajio_title(soup: BeautifulSoup) -> str | None:
    og = _meta_content(soup, prop="og:title")
    if og:
        return og
    title = soup.find("title")
    if title:
        txt = title.get_text(strip=True)
        if txt:
            return txt
    return None


def _ajio_image(soup: BeautifulSoup) -> str | None:
    og = _meta_content(soup, prop="og:image")
    if og and og.startswith("http"):
        return og
    return None


def _ajio_brand(soup: BeautifulSoup) -> str | None:
    for script in soup.find_all("script", type="application/ld+json"):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        found = brand_from_json_ld_object(data)
        if found:
            return found
    return None


def _parse_json_ld_product(soup: BeautifulSoup) -> tuple[float | None, float | None, bool, str] | None:
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError:
            continue
        candidates: list[dict[str, Any]] = []
        if isinstance(data, dict):
            candidates.append(data)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    candidates.append(item)
        for obj in candidates:
            types = obj.get("@type")
            type_names: set[str] = set()
            if isinstance(types, str):
                type_names.add(types)
            elif isinstance(types, list):
                for t in types:
                    if isinstance(t, str):
                        type_names.add(t)
            if not type_names.intersection({"Product", "ProductGroup"}):
                continue
            offers = obj.get("offers")
            price, mrp, in_stock, method = _offers_to_signal(offers, obj)
            if price is not None or in_stock:
                return price, mrp, in_stock, f"json_ld:{method}"
    return None


def _offers_to_signal(
    offers: Any,
    product_obj: dict[str, Any],
) -> tuple[float | None, float | None, bool, str]:
    """Extract selling price, optional MRP, and availability from schema.org offers."""
    price: float | None = None
    mrp: float | None = None
    in_stock = False
    method = "offers"

    def _num(x: Any) -> float | None:
        if x is None:
            return None
        if isinstance(x, (int, float)) and x > 0:
            return float(x)
        if isinstance(x, str):
            m = re.search(r"(\d+(?:\.\d+)?)", x.replace(",", ""))
            if m:
                try:
                    v = float(m.group(1))
                    return v if v > 0 else None
                except ValueError:
                    pass
        return None

    if isinstance(offers, dict):
        otype = str(offers.get("@type", "")).lower()
        if "aggregateoffer" in otype:
            low = _num(offers.get("lowPrice"))
            high = _num(offers.get("highPrice"))
            price = low or high or price
            if high and low and high > low:
                mrp = high
            elif high and not low:
                price = high
            method = "aggregate_offer"
        else:
            price = _num(offers.get("price")) or price
        avail = str(offers.get("availability", "")).lower()
        if "outofstock" in avail or "discontinued" in avail:
            in_stock = False
            method = "offers_avail"
        if "instock" in avail or "onsale" in avail or "preorder" in avail:
            in_stock = True
            method = "offers_avail"
    elif isinstance(offers, list) and offers:
        first = offers[0]
        if isinstance(first, dict):
            return _offers_to_signal(first, product_obj)

    if price is None:
        price = _num(product_obj.get("price"))

    return price, mrp, in_stock, method


def _dom_fallback(soup: BeautifulSoup) -> ParseSignal | None:
    """Last-resort: visible rupee amounts and notify-me style cues."""
    text = soup.get_text(" ", strip=True).lower()
    if "notify me" in text or "out of stock" in text:
        p = _first_rupee_price(soup)
        return ParseSignal(in_stock=False, price_inr=p, method="dom_out_of_stock")

    p = _first_rupee_price(soup)
    if p and ("add to bag" in text or "add to cart" in text):
        return ParseSignal(in_stock=True, price_inr=p, method="dom_add_to_bag")
    return None


def _first_rupee_price(soup: BeautifulSoup) -> float | None:
    for el in soup.find_all(string=re.compile(r"₹\s*[\d,]+")):
        parent_text = el.parent.get_text(" ", strip=True) if el.parent else str(el)
        m = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", parent_text)
        if m:
            try:
                v = float(m.group(1).replace(",", ""))
                if v > 0:
                    return v
            except ValueError:
                continue
    return None
