from __future__ import annotations

from stock_notifier.models import ParseContext, WebsiteConfig, WishlistItem
from stock_notifier.parsers import amazon as amazon_parser
from stock_notifier.parsers import flipkart as flipkart_parser


def _minimal_amazon_website() -> WebsiteConfig:
    return WebsiteConfig(
        key="amazon",
        display_name="Amazon",
        wishlist_products={
            "PS5": WishlistItem(name="PS5", asin="B09V59MD1P"),
        },
    )


def test_flipkart_detects_add_to_cart() -> None:
    html = '<html><body><button class="_2KpZ6l _2U9uOA _3v1-ww"> ADD TO CART</button></body></html>'
    ctx = ParseContext(
        job_product_key="PS5",
        website_key="flipkart",
        page_url="https://www.flipkart.com/p",
        website=WebsiteConfig(key="flipkart", display_name="Flipkart"),
    )
    r = flipkart_parser.parse(html, ctx)
    assert len(r.signals) == 1
    assert r.signals[0].in_stock is True
    assert r.signals[0].product_key == "PS5"


def test_amazon_wishlist_in_stock() -> None:
    html = """
    <html><body><ul>
    <li data-reposition-action-params="B09V59MD1P" data-price="49999">
      <span class="add_to_cart something">x</span>
    </li>
    </ul></body></html>
    """
    ctx = ParseContext(
        job_product_key="PS_WISHLIST",
        website_key="amazon",
        page_url="https://www.amazon.in/hz/wishlist/ls/TEST/",
        website=_minimal_amazon_website(),
    )
    r = amazon_parser.parse(html, ctx)
    by = {s.product_key: s for s in r.signals}
    assert by["PS5"].in_stock is True


def test_amazon_product_page_in_stock() -> None:
    html = """
    <html><body>
    <div id="availability"><span>In stock on</span></div>
    </body></html>
    """
    ctx = ParseContext(
        job_product_key="PS5",
        website_key="amazon",
        page_url="https://www.amazon.in/dp/B09V59MD1P",
        website=WebsiteConfig(key="amazon", display_name="Amazon"),
    )
    r = amazon_parser.parse(html, ctx)
    assert r.signals[0].in_stock is True
