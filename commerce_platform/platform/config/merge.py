"""Load YAML platform config merged with DB-backed catalog overlay."""

from __future__ import annotations

from pathlib import Path

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.config.schema import PlatformConfig, ProductConfig
from commerce_platform.platform.store.repos.catalog_repo import CatalogRepo


def merge_products(base: PlatformConfig, overlays: list[ProductConfig]) -> list[ProductConfig]:
    merged_list = list(base.products)
    by_id: dict[str, ProductConfig] = {p.id: p for p in merged_list}
    id_to_idx = {p.id: i for i, p in enumerate(merged_list)}

    for o in overlays:
        if o.id not in by_id:
            merged_list.append(o)
            id_to_idx[o.id] = len(merged_list) - 1
            by_id[o.id] = o
            continue
        cur = by_id[o.id]
        urls = {w.url for w in cur.watches}
        new_watches = list(cur.watches)
        for w in o.watches:
            if w.url not in urls:
                new_watches.append(w)
                urls.add(w.url)
        updated = cur.model_copy(
            update={
                "name": o.name,
                "brand": o.brand,
                "category": o.category,
                "emoji": o.emoji,
                "colour": o.colour,
                "image_url": o.image_url or cur.image_url,
                "watches": new_watches,
            }
        )
        idx = id_to_idx[o.id]
        merged_list[idx] = updated
        by_id[o.id] = updated

    return merged_list


async def load_merged_platform_config(yaml_path: str | Path, catalog_repo: CatalogRepo) -> PlatformConfig:
    base = load(yaml_path)
    extra = await catalog_repo.list_overlay_as_products(base.defaults)
    merged_products = merge_products(base, extra)
    return base.model_copy(update={"products": merged_products})
