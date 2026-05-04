"""Deterministic LLM stub for testing and dev."""

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
            "title": "Deal alert",
            "body_markdown": "🔥 Deal found",
            "skip_reason": None,
        }
