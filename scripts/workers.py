#!/usr/bin/env python3
"""Start the worker tasks (discovery, curation, parser fixing)."""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers


async def main() -> None:
    """Start all worker tasks."""
    load_dotenv(Path(".env"), override=True)
    config = load(Path("config.yaml"))
    db = Database(config.platform.store)

    await db.open()
    try:
        await run_stock_and_deals_workers(config, "config.yaml", db=db)
    except KeyboardInterrupt:
        print("\nWorkers stopped")
    finally:
        await db.close()


if __name__ == "__main__":
    print("")
    print("=" * 60)
    print("  Deal Discovery — Workers")
    print("=" * 60)
    print("")
    print("Starting worker tasks:")
    print("  • StockRunner (reloads config)")
    print("  • DiscoveryLoop (polls retailers)")
    print("  • CurationLoop (approves/rejects deals)")
    print("  • ParserFixerAgent (auto-fixes selectors)")
    print("")
    print("To stop: Ctrl+C")
    print("")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Workers stopped")
