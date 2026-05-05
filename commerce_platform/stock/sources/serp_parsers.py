"""Retailer listing-page parsers for deal candidate URLs.

Strategy: Extract product data using multiple fallback methods:
1. Retailer-specific CSS selectors (fastest)
2. JSON-LD structured data (most reliable)
3. Common patterns (as last resort)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ListingItem:
    """A product listing extracted from a retailer page (SERP or deals page)."""

    url: str
    title: str | None = None
    price_inr: float | None = None
    mrp_inr: float | None = None
    image_url: str | None = None
    discount_pct: float | None = None
    position: int = 0


def extract_amazon_serp_urls(page_html: str, *, max_links: int) -> list[str]:
    soup = BeautifulSoup(page_html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a.get("href") or "").strip()
        if "/dp/" not in href and "/gp/product/" not in href:
            continue
        u = _to_abs("https://www.amazon.in", href)
        if "/dp/" in u:
            u = u.split("?", 1)[0]
        if u in seen:
            continue
        seen.add(u)
        urls.append(u)
        if len(urls) >= max_links:
            break
    return urls


def extract_flipkart_serp_urls(page_html: str, *, max_links: int) -> list[str]:
    soup = BeautifulSoup(page_html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a.get("href") or "").strip()
        if "/p/" not in href:
            continue
        u = _to_abs("https://www.flipkart.com", href).split("?", 1)[0]
        if "/p/" not in u:
            continue
        if u in seen:
            continue
        seen.add(u)
        urls.append(u)
        if len(urls) >= max_links:
            break
    return urls


def extract_ajio_serp_urls(page_html: str, *, max_links: int) -> list[str]:
    soup = BeautifulSoup(page_html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a.get("href") or "").strip()
        if "/p/" not in href:
            continue
        u = _to_abs("https://www.ajio.com", href).split("?", 1)[0]
        if "/p/" not in u:
            continue
        if u in seen:
            continue
        seen.add(u)
        urls.append(u)
        if len(urls) >= max_links:
            break
    return urls


def _extract_jsonld_products(html: str) -> list[dict]:
    """Extract product data from JSON-LD structured data.

    Fallback when CSS selectors fail. Most retailers embed product info in:
    <script type="application/ld+json">{"@context": "...", "@type": "Product", ...}</script>
    """
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
            if isinstance(data, dict):
                if data.get("@type") == "Product":
                    products.append(data)
                elif data.get("@type") == "ItemList":
                    # ItemList contains multiple products
                    for item in data.get("itemListElement", []):
                        if item.get("item", {}).get("@type") == "Product":
                            products.append(item.get("item", {}))
            elif isinstance(data, list):
                products.extend([p for p in data if p.get("@type") == "Product"])
        except (json.JSONDecodeError, TypeError):
            continue

    return products


def _extract_from_jsonld(product_data: dict) -> tuple[str | None, float | None, float | None]:
    """Extract URL, price, MRP from JSON-LD product object."""
    url = product_data.get("url") or product_data.get("productID")

    # Price extraction
    price_inr = None
    if "offers" in product_data:
        offers = product_data["offers"]
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if isinstance(offers, dict):
            price_str = offers.get("price")
            if price_str:
                price_inr = _parse_price(str(price_str))

    # MRP extraction
    mrp_inr = None
    if "msrp" in product_data:
        mrp_inr = _parse_price(str(product_data["msrp"]))

    return url, price_inr, mrp_inr


def _to_abs(base: str, href: str) -> str:
    h = href.strip()
    if h.startswith("http://") or h.startswith("https://"):
        return h
    if h.startswith("//"):
        return "https:" + h
    if h.startswith("/"):
        return base + h
    return base + "/" + h


def _parse_price(text: str) -> float | None:
    """Extract numeric price from text like '₹45,990' or '$100.00'."""
    if not text:
        return None
    # Remove currency symbols and spaces, then parse
    cleaned = re.sub(r"[^\d.]", "", text)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_discount_pct(text: str) -> float | None:
    """Extract discount percentage from text like '25% off' or '25%'."""
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if match:
        return float(match.group(1)) / 100.0
    return None


def extract_amazon_deal_items(page_html: str, *, max_items: int = 50) -> list[ListingItem]:
    """Parse Amazon Deals page into ListingItems with price+discount.

    Strategy: Try CSS selectors first, fall back to JSON-LD, then raise ValueError.
    Raises ValueError if unable to extract any items (parser may be broken).
    """
    soup = BeautifulSoup(page_html, "html.parser")
    items: list[ListingItem] = []
    seen_urls: set[str] = set()

    # Strategy 1: Try CSS-based extraction
    deal_containers = (
        soup.find_all("div", class_=re.compile(r"DealCard|deal-card|dealContainer|productContainer"))
        or soup.find_all("div", class_=re.compile(r"sg-col-inner"))
        or []
    )

    for pos, container in enumerate(deal_containers[:max_items]):
        if len(items) >= max_items:
            break

        link = container.find("a", href=re.compile(r"/dp/|/gp/product/"))
        if not link or not link.get("href"):
            continue

        href = str(link.get("href")).strip()
        url = _to_abs("https://www.amazon.in", href).split("?", 1)[0]

        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Extract title, price, discount
        title = None
        price_inr = None
        mrp_inr = None
        discount_pct = None

        # Try to find price elements (retailers often use consistent class patterns)
        for span in container.find_all(re.compile(r"span|div")):
            text = span.get_text(strip=True)
            if re.search(r"₹[\d,]+", text) and price_inr is None:
                price_inr = _parse_price(text)
            if re.search(r"\d+%\s*off", text) and discount_pct is None:
                discount_pct = _parse_discount_pct(text)
            if not title and len(text) > 5 and len(text) < 200:
                title = text

        items.append(
            ListingItem(
                url=url,
                title=title,
                price_inr=price_inr,
                mrp_inr=mrp_inr,
                discount_pct=discount_pct,
                position=pos,
            )
        )

    # Strategy 2: JSON-LD fallback (if CSS extraction failed)
    if not items:
        jsonld_products = _extract_jsonld_products(page_html)
        for pos, product in enumerate(jsonld_products[:max_items]):
            url, price_inr, mrp_inr = _extract_from_jsonld(product)
            if url and price_inr:
                items.append(
                    ListingItem(
                        url=url,
                        title=product.get("name"),
                        price_inr=price_inr,
                        mrp_inr=mrp_inr,
                        discount_pct=None,
                        position=pos,
                    )
                )

    if not items:
        raise ValueError(
            "Amazon deals parser: Failed to extract any items via CSS or JSON-LD. "
            "Page structure may have changed — inspect with Playwright."
        )

    return items


def extract_flipkart_offer_items(page_html: str, *, max_items: int = 50) -> list[ListingItem]:
    """Parse Flipkart Offers page into ListingItems.

    Strategy: Try CSS selectors first, fall back to JSON-LD.
    Raises ValueError if unable to extract any items (parser may be broken).
    """
    soup = BeautifulSoup(page_html, "html.parser")
    items: list[ListingItem] = []
    seen_urls: set[str] = set()

    # Strategy 1: Find all product cards (Flipkart uses multiple class patterns)
    containers = soup.find_all("a", href=re.compile(r"/p/[A-Z0-9]"))

    for pos, link in enumerate(containers[:max_items]):
        if len(items) >= max_items:
            break

        href = str(link.get("href") or "").strip()
        url = _to_abs("https://www.flipkart.com", href).split("?", 1)[0]

        if "/p/" not in url or url in seen_urls:
            continue
        seen_urls.add(url)

        # Find parent container
        card = link.find_parent(re.compile(r"div"))
        title = None
        price_inr = None
        mrp_inr = None
        discount_pct = None

        if card:
            # Extract all text content and look for prices
            for elem in card.find_all(re.compile(r"span|div")):
                text = elem.get_text(strip=True)
                if re.search(r"₹[\d,]+", text) and price_inr is None:
                    price_inr = _parse_price(text)
                if re.search(r"\d+%\s*off", text) and discount_pct is None:
                    discount_pct = _parse_discount_pct(text)

            # Extract title (longest text that looks like a product name)
            title_candidates = [
                e.get_text(strip=True)
                for e in card.find_all(re.compile(r"span|div"))
                if 5 < len(e.get_text(strip=True)) < 150
            ]
            if title_candidates:
                title = title_candidates[0]

        items.append(
            ListingItem(
                url=url,
                title=title,
                price_inr=price_inr,
                mrp_inr=mrp_inr,
                discount_pct=discount_pct,
                position=pos,
            )
        )

    # Strategy 2: JSON-LD fallback
    if not items:
        jsonld_products = _extract_jsonld_products(page_html)
        for pos, product in enumerate(jsonld_products[:max_items]):
            url, price_inr, mrp_inr = _extract_from_jsonld(product)
            if url and price_inr:
                items.append(
                    ListingItem(
                        url=url,
                        title=product.get("name"),
                        price_inr=price_inr,
                        mrp_inr=mrp_inr,
                        discount_pct=None,
                        position=pos,
                    )
                )

    if not items:
        raise ValueError(
            "Flipkart offers parser: Failed to extract any items via CSS or JSON-LD. "
            "Page structure may have changed — inspect with Playwright."
        )

    return items


def extract_ajio_offer_items(page_html: str, *, max_items: int = 50) -> list[ListingItem]:
    """Parse Ajio Sale page into ListingItems.

    Note: Ajio uses React — CSS extraction may require proper page rendering.
    Strategy: Try CSS first, JSON-LD second.
    Raises ValueError if unable to extract any items (parser may be broken).
    """
    soup = BeautifulSoup(page_html, "html.parser")
    items: list[ListingItem] = []
    seen_urls: set[str] = set()

    # Strategy 1: Find product links
    links = soup.find_all("a", href=re.compile(r"/p/[A-Z0-9]"))

    for pos, link in enumerate(links[:max_items]):
        if len(items) >= max_items:
            break

        href = str(link.get("href") or "").strip()
        url = _to_abs("https://www.ajio.com", href).split("?", 1)[0]

        if "/p/" not in url or url in seen_urls:
            continue
        seen_urls.add(url)

        card = link.find_parent(re.compile(r"div"))
        title = None
        price_inr = None
        discount_pct = None

        if card:
            for elem in card.find_all(re.compile(r"span|div")):
                text = elem.get_text(strip=True)
                if re.search(r"₹[\d,]+", text) and price_inr is None:
                    price_inr = _parse_price(text)
                if re.search(r"\d+%\s*(?:off|discount)", text) and discount_pct is None:
                    discount_pct = _parse_discount_pct(text)

        items.append(
            ListingItem(
                url=url,
                title=link.get("aria-label") or link.get_text(strip=True)[:100] or None,
                price_inr=price_inr,
                mrp_inr=None,
                discount_pct=discount_pct,
                position=pos,
            )
        )

    # Strategy 2: JSON-LD fallback
    if not items:
        jsonld_products = _extract_jsonld_products(page_html)
        for pos, product in enumerate(jsonld_products[:max_items]):
            url, price_inr, mrp_inr = _extract_from_jsonld(product)
            if url and price_inr:
                items.append(
                    ListingItem(
                        url=url,
                        title=product.get("name"),
                        price_inr=price_inr,
                        mrp_inr=mrp_inr,
                        discount_pct=None,
                        position=pos,
                    )
                )

    if not items:
        raise ValueError(
            "Ajio sale parser: Failed to extract items via CSS or JSON-LD. "
            "Ajio uses React — may need Playwright for JS rendering."
        )

    return items


def extract_myntra_offer_items(page_html: str, *, max_items: int = 50) -> list[ListingItem]:
    """Parse Myntra Offers page into ListingItems.

    Note: Myntra uses React — CSS extraction may require proper page rendering.
    Strategy: Try CSS first, JSON-LD second.
    Raises ValueError if unable to extract any items (parser may be broken).
    """
    soup = BeautifulSoup(page_html, "html.parser")
    items: list[ListingItem] = []
    seen_urls: set[str] = set()

    # Strategy 1: Find product containers
    links = soup.find_all("a", href=re.compile(r"/products/[a-zA-Z0-9-]+"))

    for pos, link in enumerate(links[:max_items]):
        if len(items) >= max_items:
            break

        href = str(link.get("href") or "").strip()
        url = _to_abs("https://www.myntra.com", href).split("?", 1)[0]

        if "/products/" not in url or url in seen_urls:
            continue
        seen_urls.add(url)

        card = link.find_parent(re.compile(r"div"))
        title = None
        price_inr = None
        mrp_inr = None
        discount_pct = None

        if card:
            for elem in card.find_all(re.compile(r"span|div")):
                text = elem.get_text(strip=True)
                if re.search(r"₹[\d,]+", text) and price_inr is None:
                    price_inr = _parse_price(text)
                if re.search(r"\d+%\s*(?:off|discount)", text) and discount_pct is None:
                    discount_pct = _parse_discount_pct(text)

        items.append(
            ListingItem(
                url=url,
                title=link.get_text(strip=True)[:100] or None,
                price_inr=price_inr,
                mrp_inr=mrp_inr,
                discount_pct=discount_pct,
                position=pos,
            )
        )

    # Strategy 2: JSON-LD fallback
    if not items:
        jsonld_products = _extract_jsonld_products(page_html)
        for pos, product in enumerate(jsonld_products[:max_items]):
            url, price_inr, mrp_inr = _extract_from_jsonld(product)
            if url and price_inr:
                items.append(
                    ListingItem(
                        url=url,
                        title=product.get("name"),
                        price_inr=price_inr,
                        mrp_inr=mrp_inr,
                        discount_pct=None,
                        position=pos,
                    )
                )

    if not items:
        raise ValueError(
            "Myntra offers parser: Failed to extract items via CSS or JSON-LD. "
            "Myntra uses React — may need Playwright for JS rendering."
        )

    return items
