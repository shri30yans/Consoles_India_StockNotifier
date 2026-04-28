from __future__ import annotations

from bs4 import BeautifulSoup

from stock_notifier.models import ParseContext, ParseResult, StockSignal


def parse(html: str, ctx: ParseContext) -> ParseResult:
    soup = BeautifulSoup(str(html), "html.parser")
    pk = ctx.job_product_key
    add_to_cart = soup.find("button", class_="_2KpZ6l _2U9uOA _3v1-ww")
    buy_now = soup.find("button", class_="_2KpZ6l _2U9uOA ihZ75k _3AWRsL")

    if add_to_cart is not None:
        return ParseResult((StockSignal(pk, ctx.website_key, True, "Add to Cart Button"),))
    if buy_now is not None:
        return ParseResult((StockSignal(pk, ctx.website_key, True, "Buy Now Button"),))
    return ParseResult((StockSignal(pk, ctx.website_key, False, "no_buy_buttons"),))
