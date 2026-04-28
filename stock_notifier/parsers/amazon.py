from __future__ import annotations

import re

from bs4 import BeautifulSoup
from bs4.element import Tag
from lxml import html

from stock_notifier.models import ParseContext, ParseResult, StockSignal, WishlistItem


def _is_wishlist_url(url: str) -> bool:
    u = url.lower()
    return "wishlist" in u or "/hz/wishlist/" in u


def _wishlist_price_ok(list_element: Tag, item: WishlistItem) -> bool:
    if not list_element.has_attr("data-price"):
        return True
    try:
        price = float(list_element["data-price"])
    except (KeyError, ValueError, TypeError):
        return True
    if item.max_cost is not None:
        return 0 < price <= item.max_cost
    return price > 0


def parse(html: str, ctx: ParseContext) -> ParseResult:
    if _is_wishlist_url(ctx.page_url):
        return _parse_wishlist(html, ctx)
    return _parse_product_page(html, ctx)


def _parse_wishlist(page_html: str, ctx: ParseContext) -> ParseResult:
    soup = BeautifulSoup(page_html, "html.parser")
    items = ctx.website.wishlist_products or {}
    signals: list[StockSignal] = []

    for item in list(items.values()):
        asin_re = re.compile(item.asin)
        list_elements = soup.find_all("li", {"data-reposition-action-params": asin_re})
        in_stock = False
        for list_element in list_elements:
            add_to_cart = list_element.find_all("span", {"class": re.compile("add_to_cart")})
            if len(add_to_cart) > 0 and _wishlist_price_ok(list_element, item):
                in_stock = True
                break

        signals.append(
            StockSignal(
                product_key=item.name,
                website_key=ctx.website_key,
                in_stock=in_stock,
                method="Wishlist" if in_stock else "wishlist_unavailable",
            )
        )
    return ParseResult(tuple(signals))


def _parse_product_page(page_html: str, ctx: ParseContext) -> ParseResult:
    pk = ctx.job_product_key
    doc = html.fromstring(str(page_html))
    try:
        stock = doc.xpath('//*[@id="availability"]/span')
        add_to_cart = doc.xpath('//*[@id="add-to-cart-button"]')
        pre_order = doc.xpath('//*[@id="buy-now-button"]')
    except Exception:
        return ParseResult(())

    if not stock:
        return ParseResult(
            (StockSignal(pk, ctx.website_key, False, "no_availability_block"),),
        )

    text = stock[0].text or ""
    if (
        "Currently unavailable" in text
        or "We don't know when or if this item will be back in stock." in text
    ):
        return ParseResult((StockSignal(pk, ctx.website_key, False, "unavailable_text"),))

    if "In stock" in text:
        return ParseResult((StockSignal(pk, ctx.website_key, True, "availability_in_stock"),))

    if len(add_to_cart) != 0:
        return ParseResult((StockSignal(pk, ctx.website_key, True, "add_to_cart"),))

    if len(pre_order) != 0:
        return ParseResult((StockSignal(pk, ctx.website_key, True, "pre_order"),))

    return ParseResult((StockSignal(pk, ctx.website_key, False, "unknown_availability"),))
