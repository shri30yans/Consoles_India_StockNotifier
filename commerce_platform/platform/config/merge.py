"""Runtime platform config: YAML for channels, sources, and defaults; products only from the database."""

from __future__ import annotations

from pathlib import Path

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.config.schema import PlatformConfig
from commerce_platform.platform.store.repos.catalog_repo import CatalogRepo


async def load_merged_platform_config(yaml_path: str | Path, catalog_repo: CatalogRepo) -> PlatformConfig:
    """Load YAML, then replace ``products`` with rows from ``catalog_products`` / ``catalog_watches``.

    Any ``products:`` section in the YAML file is ignored at runtime — the catalog lives in the database.
    Use ``scripts/import_yaml_products_to_db.py`` once if you still have products defined only in YAML.
    """
    base = load(yaml_path)
    products = await catalog_repo.list_overlay_as_products(base.defaults)
    return base.model_copy(update={"products": products})
