"""Retailer listing-page parsers for deal candidate URLs.

Strategy: Extract product data using multiple fallback methods:
1. Retailer-specific CSS selectors (fastest)
2. JSON-LD structured data (most reliable)
3. Common patterns (as last resort)
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
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
    """Extract numeric price from text like '₹45,990' or 'Deal Price: ₹79,999.00'."""
    if not text:
        return None
    # Prefer ₹-prefixed number so strings like "M.R.P: ₹87,999.00" work correctly
    m = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    # Fallback: strip non-digit/period but only when there's a clear standalone number
    cleaned = re.sub(r"[^\d]", "", text)
    if cleaned:
        try:
            return float(cleaned)
        except ValueError:
            pass
    return None


def _parse_discount_pct(text: str) -> float | None:
    """Extract discount percentage from text like '25% off' or '25%'."""
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if match:
        return float(match.group(1)) / 100.0
    return None


_LISTING_PAGE_FAILURE_MESSAGES: dict[str, str] = {
    "amazon_deals": (
        "Amazon deals parser: Failed to extract any items via CSS or JSON-LD. "
        "Page structure may have changed — inspect with Playwright."
    ),
    "flipkart_offers": (
        "Flipkart offers parser: Failed to extract any items via CSS or JSON-LD. "
        "Page structure may have changed — inspect with Playwright."
    ),
    "ajio_sale": (
        "Ajio sale parser: Failed to extract items via CSS or JSON-LD. "
        "Ajio uses React — may need Playwright for JS rendering."
    ),
    "myntra_offers": (
        "Myntra offers parser: Failed to extract items via CSS or JSON-LD. "
        "Myntra uses React — may need Playwright for JS rendering."
    ),
}


def _extract_with_css_then_jsonld(
    *,
    page_html: str,
    css_strategy: Callable[[str], list[ListingItem]],
    max_items: int,
    retailer_label: str,
    css_min_threshold: int = 1,
) -> list[ListingItem]:
    """Run retailer-specific CSS extraction; fall back to JSON-LD; raise if both fail."""
    items = css_strategy(page_html)
    if len(items) < css_min_threshold:
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
        raise ValueError(_LISTING_PAGE_FAILURE_MESSAGES[retailer_label])
    return items[:max_items]


_AMAZON_TITLE_SKIP = re.compile(
    r"^(Limited time deal|Deal Price|M\.R\.P|Shop .+ deals?|Add to cart|₹|\d+%)",
    re.I,
)


def _amazon_deal_items_css(page_html: str, *, max_items: int) -> list[ListingItem]:
    soup = BeautifulSoup(page_html, "html.parser")
    items: list[ListingItem] = []
    seen_urls: set[str] = set()

    # Strategy 1: data-testid="product-card" — stable across Amazon redesigns
    cards = soup.find_all(attrs={"data-testid": "product-card"})

    for pos, card in enumerate(cards[:max_items]):
        if len(items) >= max_items:
            break

        link_elem = card.find(attrs={"data-testid": "product-card-link"}) or card.find(
            "a", href=re.compile(r"/dp/|/gp/product/")
        )
        if not link_elem or not link_elem.get("href"):
            continue

        href = str(link_elem["href"]).strip()
        url = _to_abs("https://www.amazon.in", href).split("?", 1)[0]
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Deal price: a-price[data-a-color="base"] → a-offscreen text e.g. "Deal Price: ₹79,999.00"
        price_inr = None
        price_span = card.find("span", attrs={"class": "a-price", "data-a-color": "base"})
        if price_span:
            os_span = price_span.find("span", class_="a-offscreen")
            if os_span:
                price_inr = _parse_price(os_span.get_text(strip=True))

        # MRP: a-price[data-a-color="secondary"] → a-offscreen text e.g. "M.R.P: ₹87,999.00"
        mrp_inr = None
        mrp_span = card.find("span", attrs={"class": "a-price", "data-a-color": "secondary"})
        if mrp_span:
            os_span = mrp_span.find("span", class_="a-offscreen")
            if os_span:
                mrp_inr = _parse_price(os_span.get_text(strip=True))

        discount_pct = None
        for t in card.find_all(string=re.compile(r"\d+%\s*off", re.I)):
            discount_pct = _parse_discount_pct(str(t))
            break

        # Title: first meaningful text string that isn't price/badge noise
        title = None
        for t in card.stripped_strings:
            s = t.strip()
            if len(s) > 15 and not _AMAZON_TITLE_SKIP.search(s):
                title = s
                break

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

    return items


def extract_amazon_deal_items(page_html: str, *, max_items: int = 50) -> list[ListingItem]:
    """Parse Amazon Deals page into ListingItems with price+discount.

    Stable selectors: data-testid="product-card" (Amazon's consistent test attribute),
    data-a-color="base/secondary" on a-price spans for deal price vs MRP.
    Raises ValueError if unable to extract any items (parser may be broken).
    """
    return _extract_with_css_then_jsonld(
        page_html=page_html,
        css_strategy=lambda h: _amazon_deal_items_css(h, max_items=max_items),
        max_items=max_items,
        retailer_label="amazon_deals",
    )


_FLIPKART_TITLE_SKIP = {"Add to Compare", "Add to Cart", "Buy Now", "Coming Soon", "Out of Stock"}


def _flipkart_offer_items_css(page_html: str, *, max_items: int) -> list[ListingItem]:
    soup = BeautifulSoup(page_html, "html.parser")
    items: list[ListingItem] = []
    seen_urls: set[str] = set()

    # Strategy 1: RGLWAk is Flipkart's product card class on search/listing pages
    cards = soup.find_all("div", class_="RGLWAk")

    for pos, card in enumerate(cards[:max_items]):
        if len(items) >= max_items:
            break

        link = card.find("a", href=re.compile(r"/p/"))
        if not link or not link.get("href"):
            continue

        href = str(link["href"]).strip()
        url = _to_abs("https://www.flipkart.com", href).split("?", 1)[0]
        if "/p/" not in url or url in seen_urls:
            continue
        seen_urls.add(url)

        # Collect all price strings in the card — first is sale price, second is MRP
        price_texts = [
            str(t).strip()
            for t in card.find_all(string=True)
            if re.search(r"₹[\d,]+", str(t))
        ]
        price_inr = _parse_price(price_texts[0]) if price_texts else None
        mrp_inr = _parse_price(price_texts[1]) if len(price_texts) >= 2 else None

        discount_pct = None
        for t in card.find_all(string=re.compile(r"\d+%\s*off", re.I)):
            discount_pct = _parse_discount_pct(str(t))
            break

        title = None
        for t in card.stripped_strings:
            s = t.strip()
            if len(s) > 15 and s not in _FLIPKART_TITLE_SKIP and "₹" not in s and "%" not in s:
                title = s
                break

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

    return items


def extract_flipkart_offer_items(page_html: str, *, max_items: int = 50) -> list[ListingItem]:
    """Parse Flipkart search/listing pages into ListingItems.

    Stable selector: div.RGLWAk (Flipkart product card class on search/listing pages).
    Seed URLs must be search or category pages — the offers/deals-today URL is JS-gated.
    Raises ValueError if unable to extract any items (parser may be broken).
    """
    return _extract_with_css_then_jsonld(
        page_html=page_html,
        css_strategy=lambda h: _flipkart_offer_items_css(h, max_items=max_items),
        max_items=max_items,
        retailer_label="flipkart_offers",
    )


def _ajio_offer_items_css(page_html: str, *, max_items: int) -> list[ListingItem]:
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
        price_inr = None
        discount_pct = None

        if card:
            for elem in card.find_all(re.compile(r"span|div")):
                text = elem.get_text(strip=True)
                if re.search(r"₹[\d,]+", text) and price_inr is None:
                    price_inr = _parse_price(text)
                if re.search(r"\d+%\s*(?:off|discount)", text) and discount_pct is None:
                    discount_pct = _parse_discount_pct(text)

        title = link.get("aria-label") or link.get_text(strip=True)[:100] or None
        items.append(
            ListingItem(
                url=url,
                title=title,
                price_inr=price_inr,
                mrp_inr=None,
                discount_pct=discount_pct,
                position=pos,
            )
        )

    return items


def extract_ajio_offer_items(page_html: str, *, max_items: int = 50) -> list[ListingItem]:
    """Parse Ajio Sale page into ListingItems.

    Note: Ajio uses React — CSS extraction may require proper page rendering.
    Strategy: Try CSS first, JSON-LD second.
    Raises ValueError if unable to extract any items (parser may be broken).
    """
    return _extract_with_css_then_jsonld(
        page_html=page_html,
        css_strategy=lambda h: _ajio_offer_items_css(h, max_items=max_items),
        max_items=max_items,
        retailer_label="ajio_sale",
    )


def _myntra_offer_items_css(page_html: str, *, max_items: int) -> list[ListingItem]:
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

        raw_title = (
            link.get("title")
            or link.get("aria-label")
            or link.get_text(strip=True)
            or ""
        ).strip()
        title = raw_title[:100] if raw_title else None
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

    return items


def extract_myntra_offer_items(page_html: str, *, max_items: int = 50) -> list[ListingItem]:
    """Parse Myntra Offers page into ListingItems.

    Note: Myntra uses React — CSS extraction may require proper page rendering.
    Strategy: Try CSS first, JSON-LD second.
    Raises ValueError if unable to extract any items (parser may be broken).
    """
    return _extract_with_css_then_jsonld(
        page_html=page_html,
        css_strategy=lambda h: _myntra_offer_items_css(h, max_items=max_items),
        max_items=max_items,
        retailer_label="myntra_offers",
    )
