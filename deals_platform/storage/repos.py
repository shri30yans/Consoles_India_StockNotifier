"""Postgres implementations of the storage ports.

Each repo gets a session factory and opens a short-lived session per call.
This is the cheapest correct pattern for asyncpg + SQLAlchemy 2.x.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from deals_platform.domain.events import PublishablePost
from deals_platform.domain.models import Money, PriceSnapshot, RetailerKey
from deals_platform.storage.schema import (
    DedupeKey,
    PostRecord,
    PriceSnapshotRow,
)


class PostgresPriceHistoryRepo:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sm = sessionmaker

    async def append(self, snap: PriceSnapshot) -> None:
        async with self._sm() as s:
            row = PriceSnapshotRow(
                canonical_id=snap.product_canonical_id,
                retailer=snap.retailer,
                price_minor=snap.price.minor_units,
                mrp_minor=snap.mrp.minor_units if snap.mrp else None,
                currency=snap.price.currency,
                in_stock=snap.in_stock,
                rating=snap.rating,
                rating_count=snap.rating_count,
                offers_json=[o.__dict__ for o in snap.offers] if snap.offers else None,
                captured_at=snap.captured_at,
            )
            s.add(row)
            await s.commit()

    async def min_since(
        self, canonical_id: str, retailer: RetailerKey, since: datetime
    ) -> Money | None:
        async with self._sm() as s:
            stmt = select(func.min(PriceSnapshotRow.price_minor)).where(
                PriceSnapshotRow.canonical_id == canonical_id,
                PriceSnapshotRow.retailer == retailer,
                PriceSnapshotRow.captured_at >= since,
                PriceSnapshotRow.in_stock.is_(True),
            )
            res = await s.scalar(stmt)
            return Money(int(res)) if res is not None else None

    async def median_since(
        self, canonical_id: str, retailer: RetailerKey, since: datetime
    ) -> Money | None:
        # Postgres percentile_cont
        async with self._sm() as s:
            stmt = select(
                func.percentile_cont(0.5)
                .within_group(PriceSnapshotRow.price_minor.asc())
                .label("median")
            ).where(
                PriceSnapshotRow.canonical_id == canonical_id,
                PriceSnapshotRow.retailer == retailer,
                PriceSnapshotRow.captured_at >= since,
                PriceSnapshotRow.in_stock.is_(True),
            )
            res = await s.scalar(stmt)
            return Money(int(res)) if res is not None else None

    async def cross_retailer_min(self, canonical_id: str) -> Money | None:
        # cheapest *current* price across retailers — uses last snapshot per retailer.
        async with self._sm() as s:
            sub = (
                select(
                    PriceSnapshotRow.retailer,
                    func.max(PriceSnapshotRow.captured_at).label("ts"),
                )
                .where(PriceSnapshotRow.canonical_id == canonical_id)
                .group_by(PriceSnapshotRow.retailer)
                .subquery()
            )
            stmt = select(func.min(PriceSnapshotRow.price_minor)).join(
                sub,
                (PriceSnapshotRow.retailer == sub.c.retailer)
                & (PriceSnapshotRow.captured_at == sub.c.ts),
            ).where(
                PriceSnapshotRow.canonical_id == canonical_id,
                PriceSnapshotRow.in_stock.is_(True),
            )
            res = await s.scalar(stmt)
            return Money(int(res)) if res is not None else None


class PostgresDedupeStore:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sm = sessionmaker

    async def seen(self, fingerprint: str) -> bool:
        async with self._sm() as s:
            stmt = select(DedupeKey).where(
                DedupeKey.fingerprint == fingerprint,
                DedupeKey.expires_at > datetime.utcnow(),
            )
            return (await s.scalar(stmt)) is not None

    async def remember(self, fingerprint: str, ttl_seconds: int) -> None:
        expires = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        async with self._sm() as s:
            stmt = (
                pg_insert(DedupeKey)
                .values(fingerprint=fingerprint, expires_at=expires)
                .on_conflict_do_update(
                    index_elements=[DedupeKey.fingerprint],
                    set_={"expires_at": expires},
                )
            )
            await s.execute(stmt)
            await s.commit()

    async def sweep(self) -> int:
        async with self._sm() as s:
            stmt = delete(DedupeKey).where(DedupeKey.expires_at <= datetime.utcnow())
            res = await s.execute(stmt)
            await s.commit()
            return res.rowcount or 0


class PostgresPostLog:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sm = sessionmaker

    async def record(self, post: PublishablePost) -> None:
        scored = post.scored
        async with self._sm() as s:
            row = PostRecord(
                canonical_id=scored.deal.canonical_id,
                category=post.category.value,
                channels=list(post.target_channels),
                title=post.title,
                body=post.body_markdown,
                affiliate_url=post.affiliate_url,
                score=scored.breakdown.score,
                score_breakdown={
                    "signals": scored.breakdown.signals,
                    "reasons": list(scored.breakdown.reasons),
                },
            )
            s.add(row)
            await s.commit()

    async def recently_posted(self, canonical_id: str, hours: int) -> bool:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        async with self._sm() as s:
            stmt = select(PostRecord.id).where(
                PostRecord.canonical_id == canonical_id,
                PostRecord.posted_at >= cutoff,
            )
            return (await s.scalar(stmt)) is not None
