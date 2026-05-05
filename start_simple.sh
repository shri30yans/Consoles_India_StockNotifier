#!/bin/bash
# Deal Discovery Platform — Startup (Linux/Mac)
# Two terminals: Backend API + Workers

echo ""
echo "==================================================================="
echo "  Deal Discovery Platform — Starting System"
echo "==================================================================="
echo ""

# Pre-flight check
echo "Verifying system..."
if ! python3 verify_system.py > /dev/null 2>&1; then
    echo ""
    echo "ERROR: System verification failed. Run: python3 verify_system.py"
    exit 1
fi
echo "OK: System verified. Starting 2 terminals..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect OS and terminal
if [[ "$OSTYPE" == "darwin"* ]]; then
    TERMINAL="Terminal"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v gnome-terminal &> /dev/null; then
        TERMINAL="gnome-terminal"
    elif command -v konsole &> /dev/null; then
        TERMINAL="konsole"
    elif command -v xterm &> /dev/null; then
        TERMINAL="xterm"
    else
        echo "ERROR: No terminal emulator found."
        exit 1
    fi
fi

# Terminal 1: API Server
echo "Starting Terminal 1: API Server (Port 8000)..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open -a Terminal << EOF
cd "$SCRIPT_DIR"
uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload
EOF
else
    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload"
            ;;
        konsole)
            konsole -e bash -c "cd '$SCRIPT_DIR' && uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload"
            ;;
        xterm)
            xterm -e bash -c "cd '$SCRIPT_DIR' && uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload"
            ;;
    esac
fi

sleep 3

# Terminal 2: Workers
echo "Starting Terminal 2: Workers..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open -a Terminal << 'EOF'
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
    await db.open()
    try:
        await run_stock_and_deals_workers(config, 'config.yaml', db=db)
    finally:
        await db.close()

asyncio.run(main())
EOF
else
    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && python3 << 'PYEOF'
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
    await db.open()
    try:
        await run_stock_and_deals_workers(config, 'config.yaml', db=db)
    finally:
        await db.close()

asyncio.run(main())
PYEOF"
            ;;
        konsole)
            konsole -e bash -c "cd '$SCRIPT_DIR' && python3 << 'PYEOF'
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
    await db.open()
    try:
        await run_stock_and_deals_workers(config, 'config.yaml', db=db)
    finally:
        await db.close()

asyncio.run(main())
PYEOF"
            ;;
        xterm)
            xterm -e bash -c "cd '$SCRIPT_DIR' && python3 << 'PYEOF'
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
    await db.open()
    try:
        await run_stock_and_deals_workers(config, 'config.yaml', db=db)
    finally:
        await db.close()

asyncio.run(main())
PYEOF"
            ;;
    esac
fi

echo ""
echo "==================================================================="
echo "  System Started"
echo "==================================================================="
echo ""
echo "Two terminals opened:"
echo "  1. API Server (Port 8000) - Serves API + Frontend"
echo "  2. Workers               - Discovery, Curation, Parser Fixing"
echo ""
echo "Next steps:"
echo "  1. Open browser: http://localhost:8000/deals"
echo "  2. Wait 60 seconds for first deal discovery"
echo "  3. Deals will appear on the page"
echo ""
echo "To stop: Close each terminal (Ctrl+C)"
echo ""
