"""Tests for Amazon PDP listing metadata on the main parse path."""

from commerce_platform.stock.parsers import amazon as amazon_parser
from commerce_platform.web.slug_suggest import suggest_product_id_from_title


def test_parse_includes_listing_metadata():
    html = """
    <html><head>
    <meta property="og:title" content="Sony PS5 Console : Amazon.in: Video Games"/>
    <meta property="og:image" content="https://m.media-amazon.com/images/I/xx.jpg"/>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Product","name":"PS5","brand":{"@type":"Brand","name":"Sony"}}
    </script>
    </head>
    <body>
    <div id="availability"><span>In stock</span></div>
    <span id="productTitle">  Sony PlayStation®5 Console (slim)  </span>
    </body></html>
    """
    signal = amazon_parser.parse(html, "https://www.amazon.in/dp/B000TEST")
    assert signal.listing_title is not None
    assert "PlayStation" in signal.listing_title
    assert signal.listing_brand == "Sony"
    assert signal.listing_image_url == "https://m.media-amazon.com/images/I/xx.jpg"


def test_suggest_product_id_from_title():
    assert suggest_product_id_from_title("Sony PS5 Console : Amazon.in: Games") == "sony_ps5_console"


def test_byline_brand():
    html = """
    <html><body>
    <div id="availability"><span>In stock</span></div>
    <a id="bylineInfo">Visit the Sony Store</a>
    <span id="productTitle">DualSense Wireless Controller</span>
    </body></html>
    """
    signal = amazon_parser.parse(html, "https://www.amazon.in/dp/B000TEST")
    assert signal.listing_brand == "Sony"
    assert signal.listing_title is not None
    assert "DualSense" in signal.listing_title
