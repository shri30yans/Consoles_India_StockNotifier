"""Data repositories — clean abstraction over asyncpg."""

from commerce_platform.platform.store.repos.catalog_repo import CatalogRepo
from commerce_platform.platform.store.repos.config_repo import ConfigSettingsRepo
from commerce_platform.platform.store.repos.deal_repo import DealRepo
from commerce_platform.platform.store.repos.price_repo import PriceRepo, PriceSnapshot
from commerce_platform.platform.store.repos.stock_repo import StockRepo
from commerce_platform.platform.store.repos.tracking_repo import TrackingRepo
from commerce_platform.platform.store.repos.user_repo import UserRepo

__all__ = [
    "CatalogRepo",
    "ConfigSettingsRepo",
    "DealRepo",
    "PriceRepo",
    "PriceSnapshot",
    "StockRepo",
    "TrackingRepo",
    "UserRepo",
]
