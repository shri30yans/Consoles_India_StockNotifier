"""Request/response bodies for the web API."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterBody":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class TrackingRequestBody(BaseModel):
    url: str = Field(min_length=12, max_length=2048)
    desired_product_name: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=2000)


class ApproveBody(BaseModel):
    product_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="tech", max_length=64)
    brand: str | None = Field(default=None, max_length=120)
    poll_seconds: int | None = None
    affiliate_tag: str | None = Field(default="env:AMAZON_AFFILIATE_TAG", max_length=120)
    image_url: str | None = Field(default=None, max_length=2048)


class RejectBody(BaseModel):
    admin_note: str | None = Field(default=None, max_length=2000)


class ListingPreviewResponse(BaseModel):
    ok: bool
    retailer: str | None = None
    reason: str | None = None
    asin: str | None = None
    fetch_url: str
    suggested_product_id: str | None = None
    name: str | None = None
    brand: str | None = None
    image_url: str | None = None
    price_inr: float | None = None
    mrp_inr: float | None = None
    in_stock: bool | None = None


class AdminProductPatchBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="tech", max_length=64)
    brand: str | None = Field(default=None, max_length=120)
    colour: int | None = None
    image_url: str | None = Field(default=None, max_length=2048)


class AdminWatchCreateBody(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=12, max_length=2048)
    asin: str | None = Field(default=None, max_length=64)
    affiliate_tag: str | None = Field(default=None, max_length=120)
    poll_seconds: int | None = Field(default=None, ge=10, le=86400 * 7)


class AdminWatchPatchBody(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=12, max_length=2048)
    asin: str | None = Field(default=None, max_length=64)
    affiliate_tag: str | None = Field(default=None, max_length=120)
    poll_seconds: int | None = Field(default=None, ge=10, le=86400 * 7)


class AdminConfigSourcePatchBody(BaseModel):
    type: str = Field(min_length=1, max_length=64)
    poll_seconds: int = Field(ge=10, le=86400 * 7)


class AdminIngestionConfigPatchBody(BaseModel):
    config_reload_seconds: int = Field(ge=5, le=86400)
    defaults_poll_seconds: int = Field(ge=10, le=86400 * 7)
    platform_sources: list[AdminConfigSourcePatchBody] = Field(default_factory=list)


class WatchResponse(BaseModel):
    """A watch entry (product URL to monitor) for API responses."""

    source: str
    url: str
    asin: str | None = None
    affiliate_tag: str | None = None
    poll_seconds: int | None = None
    db_watch_id: int | None = None


class DealsScoringConfigBody(BaseModel):
    """Deal scoring configuration request body."""

    threshold: float = Field(ge=0.0, le=1.0)
    repost_cooldown_hours: int = Field(ge=1, le=168)
    weights: dict[str, float]


class DealCardResponse(BaseModel):
    """Deal card for frontend display."""

    id: int
    product_url: str
    product_id: str | None
    retailer: str
    price_inr: float
    mrp_inr: float | None
    discount_pct: float | None
    score: float
    score_reasons: list[str]
    product_title: str | None
    image_url: str | None
    source: str
    is_active: bool
    first_seen_at: str
    last_confirmed_at: str
