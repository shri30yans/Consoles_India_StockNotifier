"""LLM adapter for any OpenAI-compatible endpoint (Gemini, OpenAI, OpenRouter, etc.)"""

from __future__ import annotations

import json
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAICompatLLM:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._key = api_key or os.environ.get("LLM_API_KEY", "")
        self._base = base_url or os.environ.get(
            "LLM_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        self._model: str = model or os.environ.get("LLM_MODEL") or "gemini-2.0-flash"
        if not self._key:
            raise RuntimeError("LLM_API_KEY is not set")
        self._client = AsyncOpenAI(api_key=self._key, base_url=self._base)

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: str,
        max_tokens: int = 600,
        temperature: float = 0.4,
    ) -> dict:
        prompt = (
            f"{user}\n\nRespond with a single JSON object matching this schema:\n{schema_hint}\n"
            "Do NOT include code fences. Do NOT include any prose outside the JSON."
        )
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = (resp.choices[0].message.content or "").strip()
        return _parse_json_loose(content)


def _parse_json_loose(text: str) -> dict:
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"LLM returned non-JSON: {text[:200]!r}")
    return json.loads(text[start : end + 1])
