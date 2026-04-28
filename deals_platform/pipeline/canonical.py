"""Canonical product resolver.

v1: deterministic hash of (brand-normalized title) so the same product across
retailers maps to the same canonical id ~most of the time. v2 can swap in an
LLM-based resolver behind the same `CanonicalResolver` port.
"""

from __future__ import annotations

import hashlib
import re

from deals_platform.domain.events import DealCandidate

_NOISE = re.compile(r"[^a-z0-9 ]+")
_MULTISPACE = re.compile(r"\s+")


def _normalize_title(title: str) -> str:
    t = title.lower()
    t = _NOISE.sub(" ", t)
    t = _MULTISPACE.sub(" ", t).strip()
    # Drop generic noise tokens.
    drop = {"buy", "online", "best", "price", "in", "india", "with", "for"}
    return " ".join(w for w in t.split() if w not in drop)


class HashCanonicalResolver:
    async def resolve(self, candidate: DealCandidate) -> str:
        basis = candidate.title or candidate.product_url
        norm = _normalize_title(basis)
        digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]
        return f"c_{digest}"
