"""Hexagonal-architecture ports. Adapters in `storage/`, `llm/`, `notify/` implement these.

Keeping ports here means the pipeline depends on *interfaces*, never on Postgres,
Gemini, or Telegram concretely. Swap any of them without touching business logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator, Protocol, runtime_checkable

from deals_platform.domain.events import (
    DealCandidate,
    EnrichedDeal,
    PublishablePost,
    ScoredDeal,
)
from deals_platform.domain.models import Money, PriceSnapshot, RetailerKey


@runtime_checkable
class Source(Protocol):
    """Anything that produces DealCandidate events.

    Sources are long-running async iterators. Implementations include retailer
    scrapers (poll product URLs) and aggregator scrapers (DesiDime, Reddit, etc).
    """

    name: str

    def stream(self) -> AsyncIterator[DealCandidate]: ...


@runtime_checkable
class PriceHistoryRepo(Protocol):
    async def append(self, snapshot: PriceSnapshot) -> None: ...
    async def min_since(
        self, canonical_id: str, retailer: RetailerKey, since: datetime
    ) -> Money | None: ...
    async def median_since(
        self, canonical_id: str, retailer: RetailerKey, since: datetime
    ) -> Money | None: ...
    async def cross_retailer_min(self, canonical_id: str) -> Money | None: ...


@runtime_checkable
class DedupeStore(Protocol):
    async def seen(self, fingerprint: str) -> bool: ...
    async def remember(self, fingerprint: str, ttl_seconds: int) -> None: ...


@runtime_checkable
class PostLog(Protocol):
    """Audit log of what we've published — used to suppress reposts and for analytics."""

    async def record(self, post: PublishablePost) -> None: ...
    async def recently_posted(self, canonical_id: str, hours: int) -> bool: ...


@runtime_checkable
class CanonicalResolver(Protocol):
    """Map a (retailer, sku/url, title) triple to a stable canonical product id."""

    async def resolve(self, candidate: DealCandidate) -> str: ...


@runtime_checkable
class Scorer(Protocol):
    def score(self, deal: EnrichedDeal) -> ScoredDeal: ...


@runtime_checkable
class CurationAgent(Protocol):
    """Decides whether/where to post, and writes the human-quality copy."""

    async def curate(self, scored: ScoredDeal) -> PublishablePost | None: ...


@runtime_checkable
class Notifier(Protocol):
    """One delivery channel (Telegram, WhatsApp, Discord, Twitter, IG, Email)."""

    name: str

    async def send(self, post: PublishablePost, channel_target: str) -> None: ...


@runtime_checkable
class LLMClient(Protocol):
    """Minimal LLM port. We don't leak provider details into business code."""

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: str,
        max_tokens: int = 600,
        temperature: float = 0.4,
    ) -> dict: ...
