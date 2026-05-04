from __future__ import annotations

from typing import Protocol


class Notifier(Protocol):
    async def send(self, text: str, chat_id: str) -> None: ...
