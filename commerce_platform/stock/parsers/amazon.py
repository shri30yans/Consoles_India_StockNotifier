"""Amazon India product page parser — extracts stock status and price."""

from __future__ import annotations

import re
from dataclasses import dataclass

from lxml import html

from commerce_platform.stock.parsers.protocol import ParseSignal


@dataclass(frozen=True)
class WishlistItem:
    asin: str
    name: str
    price_inr: float | None
    in_stock: bool


def parse(page_html: str, url: str) -> ParseSignal:
    if "wishlist" in url.lower() or "/hz/wishlist/" in url.lower():
        return _parse_wishlist(page_html)
    return _parse_product_page(page_html)


def _parse_product_page(page_html: str) -> ParseSignal:
    try:
        doc = html.fromstring(str(page_html))
    except Exception:
        return ParseSignal(in_stock=False, method="parse_error")

    # --- Stock status ---
    availability = doc.xpath('//*[@id="availability"]/span')
    add_to_cart = doc.xpath('//*[@id="add-to-cart-button"]')
    buy_now = doc.xpath('//*[@id="buy-now-button"]')

    if not availability:
        if add_to_cart:
            in_stock = True
            method = "add_to_cart_no_avail"
        else:
            return ParseSignal(in_stock=False, method="no_availability_block")
    else:
        text = (availability[0].text or "").strip()
        if "Currently unavailable" in text or "don't know when" in text:
            return ParseSignal(in_stock=False, method="unavailable_text")
        elif "In stock" in text:
            in_stock = True
            method = "availability_in_stock"
        elif add_to_cart:
            in_stock = True
            method = "add_to_cart"
        elif buy_now:
            in_stock = True
            method = "buy_now"
        else:
            return ParseSignal(in_stock=False, method="unknown_availability")

    # --- Price ---
    price = _extract_price(doc)
    mrp = _extract_mrp(doc)

    # --- Offers ---
    offers = _extract_offers(doc)

    return ParseSignal(in_stock=in_stock, price_inr=price, mrp_inr=mrp, method=method, offers=tuple(offers))


def _extract_price(doc: html.HtmlElement) -> float | None:
    selectors = [
        '//*[@id="priceblock_ourprice"]',
        '//*[@id="priceblock_dealprice"]',
        '//*[contains(@class,"a-price-whole")]',
        '//*[@id="corePrice_desktop"]//*[contains(@class,"a-price")]',
    ]
    for sel in selectors:
        nodes = doc.xpath(sel)
        if nodes:
            raw = (nodes[0].text_content() or "").strip()
            p = _rupee_to_float(raw)
            if p and p > 0:
                return p
    return None


def _extract_mrp(doc: html.HtmlElement) -> float | None:
    nodes = doc.xpath('//*[contains(@class,"a-text-strike")]')
    for n in nodes:
        p = _rupee_to_float(n.text_content() or "")
        if p and p > 0:
            return p
    return None


def _extract_offers(doc: html.HtmlElement) -> list[str]:
    offers = []
    for n in doc.xpath('//*[contains(@class,"promoPriceBlockMessage")]'):
        text = (n.text_content() or "").strip()
        if text:
            offers.append(text[:100])
    return offers[:5]


def _rupee_to_float(text: str) -> float | None:
    cleaned = re.sub(r"[₹,\s]", "", text)
    m = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _parse_wishlist(page_html: str) -> ParseSignal:
    return ParseSignal(in_stock=False, method="wishlist_use_parse_wishlist")


def parse_wishlist(page_html: str) -> list[WishlistItem]:
    """Parse Amazon India wishlist page → list of items with stock status and price."""
    try:
        doc = html.fromstring(page_html)
    except Exception:
        return []

    items = []
    for li in doc.xpath('//li[@data-id]'):
        asin = (li.get('data-asin') or li.get('data-id') or '').strip()
        if not asin:
            continue

        # Item name — multiple selectors for different wishlist page layouts
        name = ''
        for sel in [
            './/a[starts-with(@id,"itemName_")]',
            './/*[contains(@class,"a-truncate-cut")]',
            './/*[contains(@class,"g-title")]',
            './/span[contains(@class,"a-text-normal")]',
        ]:
            nodes = li.xpath(sel)
            if nodes:
                candidate = (nodes[0].text_content() or '').strip()
                if candidate:
                    name = candidate
                    break
        if not name:
            name = asin

        # Price — data-price is most reliable; fallback to DOM scraping
        price: float | None = None
        raw = (li.get('data-price') or '').strip()
        if raw and raw not in ('-Infinity', 'Infinity'):
            try:
                price = float(raw)
            except ValueError:
                pass
        if price is None:
            price = _extract_price(li)

        # Stock — add-to-cart button present = in stock; unavailability text = out of stock
        add_to_cart = li.xpath('.//input[@name="submit.addToCart"]')
        unavailable_text = li.xpath(
            './/*[contains(translate(normalize-space(text()),'
            '"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),'
            '"currently unavailable")]'
        )
        if unavailable_text:
            in_stock = False
        elif add_to_cart:
            in_stock = True
        else:
            # Treat items with a valid positive price as likely in stock when no explicit signal
            in_stock = price is not None and price > 0

        items.append(WishlistItem(
            asin=asin,
            name=name[:150],
            price_inr=price if price and price > 0 else None,
            in_stock=in_stock,
        ))

    return items
