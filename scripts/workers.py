#!/usr/bin/env python3
"""Start the worker tasks (stock polling + notification pipeline)."""

import asyncio
import sys
from pathlib import Path

from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers
from dotenv import load_dotenv

# Playwright spawns its Node driver via asyncio.create_subprocess_exec which
# only the Proactor loop supports on Windows. Python 3.8+ uses it by default,
# but set explicitly to be safe.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


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
    print("  • StockRunner  (product pollers + deal discovery watchers)")
    print("  • Observations (rule engine → notifications)")
    print("")
    print("To stop: Ctrl+C")
    print("")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Workers stopped")
