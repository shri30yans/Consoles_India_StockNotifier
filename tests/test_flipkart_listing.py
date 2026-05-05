"""Flipkart parser attaches listing metadata like Amazon."""

from commerce_platform.stock.parsers import flipkart as flipkart_parser


def test_flipkart_parse_includes_listing_metadata():
    html = """
    <html><head>
    <meta property="og:title" content="Nothing Phone (2a) - Flipkart.com"/>
    <meta property="og:image" content="https://rukmini1.flixcart.com/image/x.jpg"/>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Product","name":"Phone","brand":{"@type":"Brand","name":"Nothing"}}
    </script>
    </head>
    <body>
    <button class="_2KpZ6l _2U9uOA _3v1-ww">ADD TO CART</button>
    </body></html>
    """
    signal = flipkart_parser.parse(html, "https://www.flipkart.com/p/itm123")
    assert signal.listing_title is not None
    assert "Nothing" in signal.listing_title or "Phone" in signal.listing_title
    assert signal.listing_brand == "Nothing"
    assert signal.listing_image_url == "https://rukmini1.flixcart.com/image/x.jpg"
