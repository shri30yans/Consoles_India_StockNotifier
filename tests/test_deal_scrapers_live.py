"""Integration tests for deal scrapers — scrape real retailer sites."""

import logging

import pytest
from commerce_platform.stock.sources.serp_parsers import (
    ListingItem,
    extract_ajio_offer_items,
    extract_amazon_deal_items,
    extract_flipkart_offer_items,
    extract_myntra_offer_items,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _import_playwright():
    """Lazy import Playwright — skip tests if not installed."""
    try:
        import playwright.async_api
        return playwright.async_api
    except ImportError:
        pytest.skip("playwright not installed. Install with: pip install playwright")


@pytest.mark.asyncio
class TestAmazonDealsScraper:
    """Test real Amazon Deals page scraping."""

    async def test_extract_amazon_deal_items_real(self):
        """Fetch amazon.in/deals and extract ListingItems."""
        pw = _import_playwright()
        async with pw.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                logger.info("Fetching Amazon deals page...")
                await page.goto("https://www.amazon.in/deals", timeout=30000, wait_until="networkidle")
                html = await page.content()

                logger.info(f"Page loaded, HTML length: {len(html)}")
                items = extract_amazon_deal_items(html, max_items=20)

                logger.info(f"Extracted {len(items)} items")
                assert len(items) > 0, "Should extract at least one deal"

                # Verify structure
                for item in items[:5]:
                    assert isinstance(item, ListingItem)
                    assert item.url, f"URL missing: {item}"
                    assert item.url.startswith("https://www.amazon.in"), f"Invalid URL: {item.url}"
                    logger.info(
                        f"  {item.title or 'Unknown'}: "
                        f"₹{item.price_inr or '?'} (MRP ₹{item.mrp_inr or '?'}) "
                        f"{item.discount_pct and f'{item.discount_pct*100:.0f}% off' or ''}"
                    )

            finally:
                await browser.close()

    async def test_amazon_items_have_prices(self):
        """Verify extracted Amazon items include price data."""
        pw = _import_playwright()
        async with pw.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto("https://www.amazon.in/deals", timeout=30000, wait_until="networkidle")
                html = await page.content()
                items = extract_amazon_deal_items(html, max_items=50)

                items_with_prices = [i for i in items if i.price_inr is not None]
                logger.info(f"Items with prices: {len(items_with_prices)}/{len(items)}")
                assert len(items_with_prices) > 0, "Should extract at least some prices from deal cards"

            finally:
                await browser.close()


@pytest.mark.asyncio
class TestFlipkartOffersScraper:
    """Test real Flipkart Offers page scraping."""

    async def test_extract_flipkart_offer_items_real(self):
        """Fetch flipkart.com/offers and extract ListingItems."""
        pw = _import_playwright()
        async with pw.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                logger.info("Fetching Flipkart offers page...")
                await page.goto("https://www.flipkart.com/offers/deals-today", timeout=30000, wait_until="networkidle")
                html = await page.content()

                logger.info(f"Page loaded, HTML length: {len(html)}")
                items = extract_flipkart_offer_items(html, max_items=20)

                logger.info(f"Extracted {len(items)} items")
                assert len(items) > 0, "Should extract at least one deal from Flipkart"

                for item in items[:5]:
                    assert isinstance(item, ListingItem)
                    assert item.url, f"URL missing: {item}"
                    logger.info(
                        f"  {item.title or 'Unknown'}: "
                        f"₹{item.price_inr or '?'} {item.discount_pct and f'{item.discount_pct*100:.0f}% off' or ''}"
                    )

            finally:
                await browser.close()

    async def test_flipkart_items_have_prices(self):
        """Verify extracted Flipkart items include price data."""
        pw = _import_playwright()
        async with pw.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto("https://www.flipkart.com/offers/deals-today", timeout=30000, wait_until="networkidle")
                html = await page.content()
                items = extract_flipkart_offer_items(html, max_items=50)

                items_with_prices = [i for i in items if i.price_inr is not None]
                logger.info(f"Items with prices: {len(items_with_prices)}/{len(items)}")
                assert len(items_with_prices) > 0, "Should extract prices from Flipkart deals"

            finally:
                await browser.close()


@pytest.mark.asyncio
class TestAjioOffersScraper:
    """Test real Ajio Sale page scraping."""

    async def test_extract_ajio_offer_items_real(self):
        """Fetch ajio.com/s/sale and extract ListingItems."""
        pw = _import_playwright()
        async with pw.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                logger.info("Fetching Ajio sale page...")
                await page.goto("https://www.ajio.com/s/sale", timeout=30000, wait_until="networkidle")
                html = await page.content()

                logger.info(f"Page loaded, HTML length: {len(html)}")
                items = extract_ajio_offer_items(html, max_items=20)

                logger.info(f"Extracted {len(items)} items")
                assert len(items) > 0, "Should extract at least one deal from Ajio"

                for item in items[:5]:
                    assert isinstance(item, ListingItem)
                    assert item.url, f"URL missing: {item}"
                    logger.info(
                        f"  {item.title or 'Unknown'}: "
                        f"₹{item.price_inr or '?'} {item.discount_pct and f'{item.discount_pct*100:.0f}% off' or ''}"
                    )

            finally:
                await browser.close()


@pytest.mark.asyncio
class TestMyntraOffersScraper:
    """Test real Myntra Offers page scraping."""

    async def test_extract_myntra_offer_items_real(self):
        """Fetch myntra.com/offers and extract ListingItems."""
        pw = _import_playwright()
        async with pw.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                logger.info("Fetching Myntra offers page...")
                await page.goto("https://www.myntra.com/offers", timeout=30000, wait_until="networkidle")
                html = await page.content()

                logger.info(f"Page loaded, HTML length: {len(html)}")
                items = extract_myntra_offer_items(html, max_items=20)

                logger.info(f"Extracted {len(items)} items")
                assert len(items) > 0, "Should extract at least one deal from Myntra"

                for item in items[:5]:
                    assert isinstance(item, ListingItem)
                    assert item.url, f"URL missing: {item}"
                    logger.info(
                        f"  {item.title or 'Unknown'}: "
                        f"₹{item.price_inr or '?'} {item.discount_pct and f'{item.discount_pct*100:.0f}% off' or ''}"
                    )

            finally:
                await browser.close()
