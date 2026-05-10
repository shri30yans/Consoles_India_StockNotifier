"""Pydantic models for platform.yaml — the single config file for the entire platform."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from commerce_platform.platform.product_name import CanonicalProductName

# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------

class Money:
    """Integer-paise value to avoid float drift. 1 INR = 100 paise."""

    __slots__ = ("paise",)

    def __init__(self, paise: int) -> None:
        self.paise = paise

    @classmethod
    def from_rupees(cls, r: float) -> Money:
        return cls(round(r * 100))

    def to_rupees(self) -> float:
        return self.paise / 100

    def __str__(self) -> str:
        return f"₹{self.paise / 100:,.0f}"

    def __repr__(self) -> str:
        return f"Money(paise={self.paise})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Money) and self.paise == other.paise

    def __lt__(self, other: Money) -> bool:
        return self.paise < other.paise

    def __le__(self, other: Money) -> bool:
        return self.paise <= other.paise

    def __hash__(self) -> int:
        return hash(self.paise)


# ---------------------------------------------------------------------------
# Config models
# ---------------------------------------------------------------------------

class StoreConfig(BaseModel):
    dsn: str | None = Field(
        default=None,
        description="Postgres URI; if unset, use DATABASE_URL from the environment (server-only).",
    )


class PlatformMetaConfig(BaseModel):
    store: StoreConfig = StoreConfig()
    log_level: str = "INFO"
    log_json: bool = False
    config_reload_seconds: int = 60


class WatchConfig(BaseModel):
    source: str
    url: str
    asin: str | None = None
    affiliate_tag: str | None = None
    poll_seconds: int | None = None  # None → inherits defaults.poll_seconds


class AlertConfig(BaseModel):
    type: Literal["back_in_stock", "price_below", "discount_pct", "new_low_price"]
    threshold_inr: float | None = None
    threshold: float | None = None       # 0.0–1.0 for discount_pct
    channels: list[str]
    retailers: list[str] | None = None   # None = any retailer

    @model_validator(mode="after")
    def _check_params(self) -> AlertConfig:
        if self.type == "price_below" and self.threshold_inr is None:
            raise ValueError("price_below alert requires threshold_inr")
        if self.type == "discount_pct" and self.threshold is None:
            raise ValueError("discount_pct alert requires threshold")
        return self


class ProductConfig(BaseModel):
    id: str
    name: CanonicalProductName
    brand: str | None = None
    category: str = "tech"
    colour: int | None = None
    image_url: str | None = None
    watches: list[WatchConfig]
    alerts: list[AlertConfig] | None = None  # None → use defaults.alerts

    @field_validator("id")
    @classmethod
    def _id_slug(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"product id must be alphanumeric+underscore: {v!r}")
        return v.lower()


class DefaultsConfig(BaseModel):
    poll_seconds: int = 60
    alerts: list[AlertConfig] = []


class TelegramChannelConfig(BaseModel):
    chat_id: str


class DiscordChannelConfig(BaseModel):
    webhook_url: str


class TwitterChannelConfig(BaseModel):
    """Post to the authenticated account; OAuth env vars only (see .env.example)."""

    pass


class ChannelConfig(BaseModel):
    id: str
    name: str
    telegram: TelegramChannelConfig | None = None
    discord: DiscordChannelConfig | None = None
    twitter: TwitterChannelConfig | None = None


class PlatformSourceConfig(BaseModel):
    type: Literal[
        "amazon_serp",
        "flipkart_serp",
        "ajio_serp",
        "amazon_deals",
        "flipkart_deals",
        "ajio_deals",
        "myntra_deals",
        "desidime",
        "reddit",
        "amazon_wishlist",
    ]
    enabled: bool = True
    url: str | None = None              # required for amazon_wishlist
    wishlist_id: str | None = None      # optional stable key for routing (default: hash of url)
    channels: list[str] = []           # alert channels for amazon_wishlist back-in-stock
    poll_seconds: int = 3600
    category: str = "tech"
    minimum_discount_pct: float | None = None
    seed_urls: list[str] = []
    subreddits: list[str] = []
    max_links_per_seed: int = 50


class StockFetchConfig(BaseModel):
    jitter_max_seconds: float = 3.0
    # Cap on concurrent fast-path (APIRequestContext) fetches.
    max_concurrent_requests: int = 4
    # Cap on concurrent rendered-page fetches (each opens a Chromium Page).
    max_concurrent_playwright: int = 2
    playwright_stealth: bool = True
    playwright_locale: str = "en-IN"
    playwright_timezone_id: str = "Asia/Kolkata"
    # Path to a Playwright storage-state JSON (cookies + localStorage).
    # Generate once with: python scripts/save_browser_state.py
    # Leave null to start with a fresh session each run.
    playwright_state_file: str | None = None


class StockConfig(BaseModel):
    fetch: StockFetchConfig = StockFetchConfig()


class ScoringWeightsConfig(BaseModel):
    lowest_90d: float = 0.35
    below_30d_median: float = 0.25
    discount_vs_mrp: float = 0.10
    cross_retailer_best: float = 0.15
    has_offers: float = 0.05
    aggregator_corroborated: float = 0.10


class DealsScoringConfig(BaseModel):
    threshold: float = 0.40
    repost_cooldown_hours: int = 24
    weights: ScoringWeightsConfig = ScoringWeightsConfig()


class DealsCurationConfig(BaseModel):
    use_llm: bool = False
    approval_required: bool = True
    approval_timeout_seconds: int = 1800
    admin_channel: str = "admin"


class DealsConfig(BaseModel):
    scoring: DealsScoringConfig = DealsScoringConfig()
    curation: DealsCurationConfig = DealsCurationConfig()
    routing: dict[str, list[str]] = {}


class PlatformConfig(BaseModel):
    platform: PlatformMetaConfig = PlatformMetaConfig()
    defaults: DefaultsConfig = DefaultsConfig()
    products: list[ProductConfig] = []
    channels: list[ChannelConfig] = []
    platform_sources: list[PlatformSourceConfig] = []
    stock: StockConfig = StockConfig()
    deals: DealsConfig = DealsConfig()
    admin_emails: list[str] = Field(default_factory=list, description="Email addresses that should have admin role")

    def resolve_poll_seconds(self, watch: WatchConfig) -> int:
        return watch.poll_seconds if watch.poll_seconds is not None else self.defaults.poll_seconds

    def resolve_alerts(self, product: ProductConfig) -> list[AlertConfig]:
        if product.alerts is not None:
            return product.alerts
        return self.defaults.alerts

    def channel_map(self) -> dict[str, ChannelConfig]:
        return {c.id: c for c in self.channels}

    def product_map(self) -> dict[str, ProductConfig]:
        return {p.id: p for p in self.products}
