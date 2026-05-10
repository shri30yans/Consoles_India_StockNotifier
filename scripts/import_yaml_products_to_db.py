"""One-time migration: copy ``products:`` from ``config.yaml`` into ``catalog_products`` / ``catalog_watches``.

The HTTP API and workers read the catalog from the database only; YAML ``products`` is ignored at runtime.
After this import succeeds, set ``products: []`` in your YAML (or remove the key) to avoid confusion.

Usage::

    python scripts/import_yaml_products_to_db.py

Environment: ``PLATFORM_CONFIG`` (default ``config.yaml``), ``DATABASE_URL`` / store DSN as usual.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import CatalogRepo
from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()
    config_path = Path(os.environ.get("PLATFORM_CONFIG", "config.yaml")).resolve()
    cfg = load(config_path)
    db = Database(cfg.platform.store)
    await db.open()
    repo = CatalogRepo(db.pool)

    items = cfg.products
    if not items:
        print(f"No products in {config_path} — nothing to import.")
        await db.close()
        return

    for p in items:
        await repo.upsert_product(
            product_id=p.id,
            name=p.name,
            brand=p.brand,
            category=p.category,
            colour=p.colour,
            image_url=p.image_url,
        )
        print(f"Upserted product {p.id}")
        for w in p.watches:
            wid = await repo.upsert_watch_by_product_url(
                product_id=p.id,
                source=w.source,
                url=w.url,
                asin=w.asin,
                affiliate_tag=w.affiliate_tag,
                poll_seconds=w.poll_seconds,
            )
            print(f"  watch id={wid} {w.source}")

    await db.close()
    print(f"\nDone. Imported {len(items)} product(s). Set products: [] in {config_path} when ready.")


if __name__ == "__main__":
    asyncio.run(main())
