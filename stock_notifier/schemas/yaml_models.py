from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from stock_notifier.models import AppConfig, ProductConfig, WebsiteConfig, WishlistItem


class PathsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    logs_dir: str = "logs"


class LoggingModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    json_lines: bool = False
    max_bytes: int = Field(default=10_485_760, ge=4096)
    backup_count: int = Field(default=5, ge=0)


class FetchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    jitter_max_seconds: float = Field(default=0.0, ge=0.0, le=300.0)
    max_concurrent_per_transport: int = Field(default=0, ge=0, le=256)
    use_fake_useragent: bool = True
    http_client: Literal["aiohttp", "curl_cffi"] = "aiohttp"
    curl_impersonate: str = Field(default="chrome124", min_length=1, max_length=64)
    playwright_apply_stealth: bool = True
    playwright_locale: str = Field(default="en-IN", min_length=2, max_length=32)
    playwright_timezone_id: str = Field(default="Asia/Kolkata", min_length=2, max_length=64)


class AppYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notify: bool = True
    mode: str = "requests"
    amazon_affiliate_tag: str = ""
    telegram_chat_id: str = ""
    paths: PathsModel = Field(default_factory=PathsModel)
    logging: LoggingModel = Field(default_factory=LoggingModel)
    fetch: FetchModel = Field(default_factory=FetchModel)

    @field_validator("mode")
    @classmethod
    def mode_lower(cls, v: str) -> str:
        return str(v).lower()


class JobRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_key: str = Field(min_length=1)
    website_key: str = Field(min_length=1)
    delay_seconds: int = Field(ge=1, le=86400)


class JobsYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str | None = None
    requests: list[JobRow] = Field(default_factory=list)
    playwright: list[JobRow] = Field(default_factory=list)


class WishlistRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    asin: str = Field(min_length=1)
    max_cost: float | None = None


class WebsiteYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1)
    display_name: str = ""
    wishlist_link: str | None = None
    wishlist_products: dict[str, WishlistRow] = Field(default_factory=dict)
    headers: list[dict[str, str]] | None = None


class WebsiteFileRoot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    website: WebsiteYaml


class ProductBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1)
    name: str = ""
    display_name: str = ""
    links: dict[str, str] = Field(default_factory=dict)
    hidden: bool = False
    subproducts: list[str] = Field(default_factory=list)
    notification_roles: dict[str, int] | None = None
    notification_channels: dict[str, int] | None = None
    affiliate_links: dict[str, str] | None = None
    add_to_cart_links: dict[str, str] | None = None
    wishlist: str | None = None
    twitter_hashtags: str = ""
    thumbnail_link: str | None = None
    colour: int = 0
    emoji: str = ""


class ProductFileRoot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product: ProductBody


def _load_yaml_dict(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_app_yaml(path: Path, *, amazon_affiliate_tag_override: str | None = None) -> AppConfig:
    raw = _load_yaml_dict(path)
    doc = AppYaml.model_validate(raw)
    tag = doc.amazon_affiliate_tag
    if amazon_affiliate_tag_override and str(amazon_affiliate_tag_override).strip():
        tag = str(amazon_affiliate_tag_override).strip()
    log_json = doc.logging.json_lines
    if os.environ.get("LOG_JSON", "").lower() in ("1", "true", "yes"):
        log_json = True
    return AppConfig(
        notify=doc.notify,
        mode=doc.mode,
        amazon_affiliate_tag=str(tag),
        telegram_chat_id=doc.telegram_chat_id,
        logs_dir=doc.paths.logs_dir,
        log_json=log_json,
        log_max_bytes=doc.logging.max_bytes,
        log_backup_count=doc.logging.backup_count,
        jitter_max_seconds=doc.fetch.jitter_max_seconds,
        max_concurrent_per_transport=doc.fetch.max_concurrent_per_transport,
        use_fake_useragent=doc.fetch.use_fake_useragent,
        http_client=doc.fetch.http_client,
        curl_impersonate=doc.fetch.curl_impersonate,
        playwright_apply_stealth=doc.fetch.playwright_apply_stealth,
        playwright_locale=doc.fetch.playwright_locale,
        playwright_timezone_id=doc.fetch.playwright_timezone_id,
    )


def parse_jobs_yaml(path: Path) -> JobsYaml:
    return JobsYaml.model_validate(_load_yaml_dict(path))


def parse_website_file(path: Path) -> WebsiteConfig:
    raw = _load_yaml_dict(path)
    root = WebsiteFileRoot.model_validate(raw)
    w = root.website
    wl: dict[str, WishlistItem] = {}
    for k, row in w.wishlist_products.items():
        wl[k] = WishlistItem(name=row.name, asin=row.asin, max_cost=row.max_cost)
    headers = [dict(h) for h in w.headers] if w.headers is not None else None
    return WebsiteConfig(
        key=w.key,
        display_name=w.display_name or w.key,
        wishlist_link=w.wishlist_link,
        wishlist_products=wl,
        headers=headers,
    )


def _int_key_map(d: dict[str, int] | None) -> dict[int, int] | None:
    if not d:
        return None
    return {int(k): int(v) for k, v in d.items()}


def parse_product_file(path: Path) -> ProductConfig:
    raw = _load_yaml_dict(path)
    root = ProductFileRoot.model_validate(raw)
    p = root.product
    stem = path.stem
    if p.key != stem:
        raise ValueError(f"Product file {path}: key {p.key!r} must match filename stem {stem!r}")
    return ProductConfig(
        key=p.key,
        name=p.name or p.key,
        display_name=p.display_name or p.key,
        links=dict(p.links),
        hidden=p.hidden,
        subproducts=tuple(p.subproducts),
        notification_roles=_int_key_map(p.notification_roles),
        notification_channels=_int_key_map(p.notification_channels),
        affiliate_links=dict(p.affiliate_links) if p.affiliate_links else None,
        add_to_cart_links=dict(p.add_to_cart_links) if p.add_to_cart_links else None,
        wishlist=p.wishlist,
        twitter_hashtags=p.twitter_hashtags,
        thumbnail_link=p.thumbnail_link,
        colour=p.colour,
        emoji=p.emoji,
    )
