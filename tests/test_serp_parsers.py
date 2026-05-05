from commerce_platform.stock.sources.serp_parsers import (
    extract_ajio_serp_urls,
    extract_amazon_serp_urls,
    extract_flipkart_serp_urls,
)


def test_extract_amazon_serp_urls() -> None:
    html = """
    <a href="/dp/B08FC5L3RG?ref_=abc">PS5</a>
    <a href="https://www.amazon.in/gp/product/B09FZ6HSQG/">PS5 Digital</a>
    """
    urls = extract_amazon_serp_urls(html, max_links=10)
    assert "https://www.amazon.in/dp/B08FC5L3RG" in urls
    assert any("/gp/product/B09FZ6HSQG/" in u for u in urls)


def test_extract_flipkart_serp_urls() -> None:
    html = """
    <a href="/sony-playstation-5/p/itm8842e69d8349e?pid=GMC">PS5</a>
    <a href="https://www.flipkart.com/xbox-series-x/p/itmf98b53e3bc98b">XSX</a>
    """
    urls = extract_flipkart_serp_urls(html, max_links=10)
    assert "https://www.flipkart.com/sony-playstation-5/p/itm8842e69d8349e" in urls
    assert "https://www.flipkart.com/xbox-series-x/p/itmf98b53e3bc98b" in urls


def test_extract_ajio_serp_urls() -> None:
    html = """
    <a href="/p/469955188_white">Sneaker</a>
    <a href="https://www.ajio.com/p/469955189_black?foo=1">Sneaker 2</a>
    """
    urls = extract_ajio_serp_urls(html, max_links=10)
    assert "https://www.ajio.com/p/469955188_white" in urls
    assert "https://www.ajio.com/p/469955189_black" in urls

