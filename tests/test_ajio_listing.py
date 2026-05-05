"""AJIO parser attaches listing metadata for admin prefill flow."""

from commerce_platform.stock.parsers import ajio as ajio_parser


def test_ajio_parse_includes_listing_metadata() -> None:
    html = """
    <html>
      <head>
        <meta property="og:title" content="Nike Air Sneakers - AJIO"/>
        <meta property="og:image" content="https://assets.ajio.com/media/x.jpg"/>
        <script type="application/ld+json">
          {"@context":"https://schema.org","@type":"Product","brand":{"@type":"Brand","name":"Nike"}}
        </script>
      </head>
      <body>
        <script type="application/ld+json">
          {"@context":"https://schema.org","@type":"Product","offers":{"price":"2999","availability":"https://schema.org/InStock"}}
        </script>
      </body>
    </html>
    """
    signal = ajio_parser.parse(html, "https://www.ajio.com/p/test-sku")
    assert signal.listing_title is not None
    assert "Nike Air Sneakers" in signal.listing_title
    assert signal.listing_brand == "Nike"
    assert signal.listing_image_url == "https://assets.ajio.com/media/x.jpg"
    assert signal.price_inr == 2999.0
    assert signal.in_stock is True

