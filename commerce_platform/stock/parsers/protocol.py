"""Parser protocol — each retailer parser implements this interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ParseSignal:
    in_stock: bool
    price_inr: float | None = None
    mrp_inr: float | None = None
    method: str = ""
    offers: tuple[str, ...] = ()


class Parser(Protocol):
    def parse(self, html: str, url: str) -> ParseSignal: ...
