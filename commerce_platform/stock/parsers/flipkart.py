"""Flipkart product page parser — extracts stock status and price."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from commerce_platform.stock.parsers.protocol import ParseSignal


def parse(page_html: str, url: str) -> ParseSignal:
    soup = BeautifulSoup(str(page_html), "html.parser")

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
                return ParseSignal(in_stock=True, method="add_to_cart_text", price_inr=_extract_price(soup))
            if "buy now" in text:
                return ParseSignal(in_stock=True, method="buy_now_text", price_inr=_extract_price(soup))
        return ParseSignal(in_stock=False, method="no_buy_buttons")

    return ParseSignal(in_stock=in_stock, method=method, price_inr=_extract_price(soup), mrp_inr=_extract_mrp(soup))


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
