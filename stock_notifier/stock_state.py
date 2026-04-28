from __future__ import annotations


class ContinuousStockState:
    """
    Tracks last known in-stock state per (product_key, website_key).
    Used to avoid repeat notifications while availability stays high.
    """

    def __init__(self) -> None:
        self._data: dict[str, dict[str, bool]] = {}

    def is_continuously_in_stock(self, product_key: str, website_key: str) -> bool:
        return bool(self._data.get(product_key, {}).get(website_key, False))

    def set_in_stock(self, product_key: str, website_key: str, value: bool) -> None:
        if product_key not in self._data:
            self._data[product_key] = {}
        self._data[product_key][website_key] = value
