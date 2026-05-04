"""One-off: rewrite catalog_products.name using normalize_product_name (encoding + spacing fixes)."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import CatalogRepo


async def run(config_path: Path) -> None:
    config = load(config_path)
    db = Database(config.platform.store)
    await db.open()
    try:
        repo = CatalogRepo(db.pool)
        changed = await repo.normalize_stored_product_names()
        if not changed:
            print("No catalog_products rows needed updating.")
            return
        print(f"Updated {len(changed)} product name(s):\n")
        for pid, old, new in changed:
            print(f"  {pid}")
            print(f"    from: {old!r}")
            print(f"    to:   {new!r}\n")
    finally:
        await db.close()


def main() -> None:
    load_dotenv()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("PLATFORM_CONFIG", "config.yaml")).resolve(),
        help="Path to config.yaml (default: PLATFORM_CONFIG or ./config.yaml)",
    )
    args = p.parse_args()
    asyncio.run(run(args.config))


if __name__ == "__main__":
    main()
