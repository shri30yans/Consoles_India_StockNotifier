"""Flipkart product page parser — extracts stock status, price, and listing metadata."""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from commerce_platform.platform.product_name import coerce_product_name
from commerce_platform.stock.parsers.json_ld_brand import brand_from_json_ld_object
from commerce_platform.stock.parsers.protocol import ListingSnapshot, ParseSignal

_FLIPKART_TITLE_SUFFIX = re.compile(
    r"\s*[-–—]\s*Flipkart(?:\.com)?.*$|\s*:\s*Flipkart(?:\.com)?.*$",
    re.IGNORECASE,
)


def parse(page_html: str, url: str) -> ParseSignal:
    soup = BeautifulSoup(str(page_html), "html.parser")
    listing = _flipkart_listing_snapshot(soup)

    # --- Stock buttons ---
    add_to_cart = soup.find("button", class_="_2KpZ6l _2U9uOA _3v1-ww")
    buy_now = soup.find("button", class_="_2KpZ6l _2U9uOA ihZ75k _3AWRsL")

    if add_to_cart is not None:
        in_stock = True
        method = "add_to_cart"
    elif buy_now is not None:
        in_stock = True
        method = "buy_now"
    else:
        # Fallback: look for any "Add to Cart" or "Buy Now" text button
        for btn in soup.find_all("button"):
            text = btn.get_text(strip=True).lower()
            if "add to cart" in text:
                return ParseSignal(
                    in_stock=True,
                    method="add_to_cart_text",
                    price_inr=_extract_price(soup),
                    listing=listing,
                )
            if "buy now" in text:
                return ParseSignal(
                    in_stock=True,
                    method="buy_now_text",
                    price_inr=_extract_price(soup),
                    listing=listing,
                )
        return ParseSignal(in_stock=False, method="no_buy_buttons", listing=listing)

    return ParseSignal(
        in_stock=in_stock,
        method=method,
        price_inr=_extract_price(soup),
        mrp_inr=_extract_mrp(soup),
        listing=listing,
    )


def _extract_price(soup: BeautifulSoup) -> float | None:
    # Flipkart price is in ._30jeq3 or ._16Jk6d
    for cls in ["_30jeq3", "_16Jk6d", "Nx9bqj"]:
        el = soup.find(class_=cls)
        if el:
            p = _rupee_to_float(el.get_text())
            if p and p > 0:
                return p
    return None


def _extract_mrp(soup: BeautifulSoup) -> float | None:
    for cls in ["_3I9_wc", "yRaY8j"]:
        el = soup.find(class_=cls)
        if el:
            p = _rupee_to_float(el.get_text())
            if p and p > 0:
                return p
    return None


def _rupee_to_float(text: str) -> float | None:
    cleaned = re.sub(r"[₹,\s]", "", text)
    m = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _flipkart_listing_snapshot(soup: BeautifulSoup) -> ListingSnapshot | None:
    title = _fk_title(soup)
    brand = _fk_brand(soup)
    image_url = _fk_image(soup)

    if title:
        title = coerce_product_name(title)
        title = _FLIPKART_TITLE_SUFFIX.sub("", title).strip() or None

    if brand:
        brand = coerce_product_name(brand.strip()) or None

    if not title and not brand and not image_url:
        return None
    return ListingSnapshot(title=title, brand=brand, image_url=image_url)


def _fk_meta_content(soup: BeautifulSoup, *, prop: str | None = None, name: str | None = None) -> str | None:
    if prop:
        m = soup.find("meta", attrs={"property": prop})
    elif name:
        m = soup.find("meta", attrs={"name": name})
    else:
        return None
    if not m:
        return None
    c = m.get("content")
    if isinstance(c, str) and c.strip():
        return c.strip()
    return None


def _fk_title(soup: BeautifulSoup) -> str | None:
    t = _fk_meta_content(soup, prop="og:title")
    if t:
        return t
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(strip=True)
        if text:
            return text
    tit = soup.find("title")
    if tit:
        text = tit.get_text(strip=True)
        if text:
            return text
    return None


def _fk_image(soup: BeautifulSoup) -> str | None:
    u = _fk_meta_content(soup, prop="og:image")
    if u and u.startswith("http"):
        return u
    return None


def _fk_brand(soup: BeautifulSoup) -> str | None:
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

    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True).lower()
        if label == "brand":
            return cells[1].get_text(strip=True)[:120] or None

    return None
