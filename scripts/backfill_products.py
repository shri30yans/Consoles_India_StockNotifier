"""One-time backfill: Load products from JSON into database."""

import asyncio
import json
from pathlib import Path
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import CatalogRepo


async def backfill_products(config_path: Path, json_path: Path) -> None:
    """Load products from JSON file into database via repository (auto-normalizes names)."""
    # Load config and connect to DB
    config = load(config_path)
    db = Database(config.platform.store)
    await db.open()

    # Read products from JSON
    with open(json_path) as f:
        data = json.load(f)

    products = data.get("products", [])
    if not products:
        print("No products found in JSON file!")
        await db.close()
        return

    catalog_repo = CatalogRepo(db.pool)

    for product in products:
        product_id = product["id"]
        try:
            # Use repository method — automatically normalizes product name
            await catalog_repo.upsert_product(
                product_id=product_id,
                name=product["name"],
                brand=product.get("brand"),
                category=product.get("category", "tech"),
                emoji=product.get("emoji"),
                colour=None,
                image_url=product.get("image_url"),
            )
            print(f"[OK] Added product: {product_id}")
        except Exception as e:
            if "duplicate key" in str(e).lower():
                print(f"[EXISTS] Product already exists: {product_id}")
            else:
                print(f"[ERROR] Error adding product {product_id}: {e}")
                continue

        # Insert watches
        watches = product.get("watches", [])
        for watch in watches:
            try:
                await catalog_repo.insert_watch(
                    product_id=product_id,
                    source=watch.get("source"),
                    url=watch.get("url"),
                    asin=watch.get("asin"),
                    affiliate_tag=watch.get("affiliate_tag"),
                    poll_seconds=watch.get("poll_seconds"),
                )
                print(f"  - Watch: {watch.get('source')} @ {watch.get('url')[:50]}...")
            except Exception as e:
                print(f"  [ERROR] Error adding watch: {e}")

    await db.close()
    print(f"\n[DONE] Backfill complete! {len(products)} products loaded.")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    config_path = Path(os.environ.get("PLATFORM_CONFIG", "config.yaml")).resolve()
    json_path = Path(__file__).parent / "products.json"

    print(f"Loading from: {json_path}")
    print(f"Config: {config_path}")
    asyncio.run(backfill_products(config_path, json_path))
