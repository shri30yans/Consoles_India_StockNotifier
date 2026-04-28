from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable


@runtime_checkable
class HtmlFetcher(Protocol):
    """HTTP(S) HTML fetch for the ``requests`` transport."""

    async def start(self) -> None: ...

    async def close(self) -> None: ...

    async def get_html(
        self,
        url: str,
        headers_pool: Iterable[dict[str, str]] | None,
        *,
        product_key: str,
        website_key: str,
    ) -> str | None: ...
