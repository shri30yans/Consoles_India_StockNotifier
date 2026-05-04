"""Request/response bodies for the web API."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


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


class AdminProductPatchBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="tech", max_length=64)
    brand: str | None = Field(default=None, max_length=120)
    emoji: str | None = Field(default=None, max_length=32)
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


class WatchResponse(BaseModel):
    """A watch entry (product URL to monitor) for API responses."""

    source: str
    url: str
    asin: str | None = None
    affiliate_tag: str | None = None
    poll_seconds: int | None = None
    db_watch_id: int | None = None
