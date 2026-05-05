#!/bin/bash
# Terminal 2: Workers (Discovery, Curation, Parser Fixing)

set -e

echo ""
echo "==================================================================="
echo "  Deal Discovery — Workers (Terminal 2)"
echo "==================================================================="
echo ""
echo "Starting worker tasks:"
echo "  • StockRunner (reloads config every 15s)"
echo "  • ObservationProcessor (processes price events)"
echo "  • DiscoveryLoop (polls retailers every 60 min)"
echo "  • CurationLoop (reviews pending deals every 5 min)"
echo "  • ParserFixerAgent (auto-fixes broken parsers)"
echo ""
echo "Expected output:"
echo "  INFO: stock-runner started"
echo "  INFO: discovery-loop started"
echo "  INFO: curation-loop started"
echo "  INFO: parser-fixer started"
echo ""
echo "Press Ctrl+C to stop."
echo ""

cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1

python3 << 'EOF'
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers

load_dotenv(Path('.env'), override=True)
config = load(Path('config.yaml'))
db = Database(config.platform.store)

async def main():
    try:
        await db.open()
        await run_stock_and_deals_workers(config, 'config.yaml', db=db)
    except KeyboardInterrupt:
        print("\nWorkers stopped")
    finally:
        await db.close()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Workers stopped")
EOF

trap "echo 'Workers stopped'; exit 0" EXIT
