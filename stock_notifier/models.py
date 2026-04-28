from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WishlistItem:
    """Single ASIN tracked on an Amazon wishlist HTML page."""

    name: str
    asin: str
    max_cost: float | None = None


@dataclass(frozen=True)
class WebsiteConfig:
    """Per-retailer settings loaded from config/websites/<key>.yaml."""

    key: str
    display_name: str
    wishlist_link: str | None = None
    wishlist_products: dict[str, WishlistItem] = field(default_factory=dict)
    headers: list[dict[str, str]] | None = None


@dataclass(frozen=True)
class ProductConfig:
    """Single SKU / logical product from config/products/<key>.yaml."""

    key: str
    name: str
    display_name: str
    links: dict[str, str]
    hidden: bool = False
    subproducts: tuple[str, ...] = ()
    notification_roles: dict[int, int] | None = None
    notification_channels: dict[int, int] | None = None
    affiliate_links: dict[str, str] | None = None
    add_to_cart_links: dict[str, str] | None = None
    wishlist: str | None = None
    twitter_hashtags: str = ""
    thumbnail_link: str | None = None
    colour: int = 0
    emoji: str = ""


@dataclass(frozen=True)
class JobSpec:
    transport: str  # "requests" | "playwright"
    product_key: str
    website_key: str
    delay_seconds: int


@dataclass(frozen=True)
class AppConfig:
    notify: bool
    mode: str
    amazon_affiliate_tag: str
    telegram_chat_id: str
    logs_dir: str
    log_json: bool = False
    log_max_bytes: int = 10_485_760
    log_backup_count: int = 5
    jitter_max_seconds: float = 0.0
    max_concurrent_per_transport: int = 0
    # HTTP fetch tuning
    use_fake_useragent: bool = True
    http_client: str = "aiohttp"  # "aiohttp" | "curl_cffi"
    curl_impersonate: str = "chrome124"
    # Playwright context / stealth
    playwright_apply_stealth: bool = True
    playwright_locale: str = "en-IN"
    playwright_timezone_id: str = "Asia/Kolkata"


@dataclass(frozen=True)
class StockSignal:
    """Outcome of parsing one logical product on one site."""

    product_key: str
    website_key: str
    in_stock: bool
    method: str


@dataclass(frozen=True)
class ParseResult:
    signals: tuple[StockSignal, ...]


@dataclass(frozen=True)
class ParseContext:
    """Everything a parser needs beyond raw HTML."""

    job_product_key: str
    website_key: str
    page_url: str
    website: WebsiteConfig
    wishlist_items: dict[str, WishlistItem] | None = None
