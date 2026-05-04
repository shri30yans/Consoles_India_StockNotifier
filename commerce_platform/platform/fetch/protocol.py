"""HtmlFetcher protocol — the single interface all transport adapters implement."""

from __future__ import annotations

from typing import Protocol


class HtmlFetcher(Protocol):
    async def get_html(
        self,
        url: str,
        *,
        label: str = "",
    ) -> str | None: ...

    async def start(self) -> None: ...

    async def close(self) -> None: ...
