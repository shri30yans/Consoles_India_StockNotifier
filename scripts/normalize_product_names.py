"""CLI migration: updates ``catalog_products.name`` using ``coerce_product_name`` (not imported by the app)."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.product_name import coerce_product_name
from commerce_platform.platform.store.db import Database
from dotenv import load_dotenv


async def run(config_path: Path) -> None:
    config = load(config_path)
    db = Database(config.platform.store)
    await db.open()
    try:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, name FROM catalog_products ORDER BY id")
        changes: list[tuple[str, str, str]] = []
        for r in rows:
            old = r["name"]
            new = coerce_product_name(old)
            if new != old:
                changes.append((str(r["id"]), old, new))
        if not changes:
            print("No catalog_products rows needed updating.")
            return
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                for pid, _old, new in changes:
                    await conn.execute(
                        "UPDATE catalog_products SET name = $1 WHERE id = $2",
                        new,
                        pid,
                    )
        print(f"Updated {len(changes)} product name(s):\n")
        for pid, old, new in changes:
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
