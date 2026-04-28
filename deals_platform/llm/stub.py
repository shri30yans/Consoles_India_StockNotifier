"""Deterministic LLM stub — handy for tests and offline dev."""

from __future__ import annotations


class StubLLM:
    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: str,
        max_tokens: int = 600,
        temperature: float = 0.4,
    ) -> dict:
        return {
            "publish": True,
            "category": "tech",
            "title": "Stub deal",
            "body_markdown": "🔥 **Stub price** — deterministic stub LLM",
            "skip_reason": None,
        }
