"""SQLAlchemy ORM schema. Tables are created via Alembic in production;
`Base.metadata.create_all` is fine for dev bootstrap.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    """Canonical product (cross-retailer)."""

    __tablename__ = "products"

    canonical_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str | None] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    image_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProductListing(Base):
    """Per-retailer SKU pointing at a canonical product."""

    __tablename__ = "product_listings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    canonical_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("products.canonical_id"), index=True
    )
    retailer: Mapped[str] = mapped_column(String(32), index=True)
    retailer_sku: Mapped[str] = mapped_column(String(128), index=True)
    product_url: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        Index("ix_listing_unique", "retailer", "retailer_sku", unique=True),
    )


class PriceSnapshotRow(Base):
    """Append-only price history. Indexed for range scans."""

    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    canonical_id: Mapped[str] = mapped_column(String(64), index=True)
    retailer: Mapped[str] = mapped_column(String(32), index=True)
    price_minor: Mapped[int] = mapped_column(BigInteger)
    mrp_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[float | None] = mapped_column(Float)
    rating_count: Mapped[int | None] = mapped_column(Integer)
    offers_json: Mapped[dict | None] = mapped_column(JSON)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    __table_args__ = (
        Index("ix_snap_canon_time", "canonical_id", "retailer", "captured_at"),
    )


class DedupeKey(Base):
    """Idempotency keys with TTL (logical TTL, swept by a periodic task)."""

    __tablename__ = "dedupe_keys"

    fingerprint: Mapped[str] = mapped_column(String(256), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class PostRecord(Base):
    """Audit log of every published deal post."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    canonical_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    channels: Mapped[list] = mapped_column(JSON)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    affiliate_url: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    score_breakdown: Mapped[dict] = mapped_column(JSON)
    posted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
