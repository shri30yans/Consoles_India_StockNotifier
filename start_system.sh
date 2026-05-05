#!/bin/bash
# Deal Discovery Platform — Complete System Startup

set -e

echo "==================================================================="
echo "  Deal Discovery Platform — System Startup"
echo "==================================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "WARNING: PostgreSQL psql not found (database may not be accessible)"
fi

if ! command -v node &> /dev/null; then
    echo "WARNING: Node.js not found (frontend won't be built)"
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"

# Initialize database if needed
echo -e "${BLUE}Checking database...${NC}"
if ! python3 -c "from commerce_platform.platform.store.db import Database; print('DB module OK')" 2>/dev/null; then
    echo "ERROR: Cannot import database module"
    exit 1
fi
echo -e "${GREEN}✓ Database module OK${NC}"

# Show startup commands
echo ""
echo -e "${BLUE}To start the system, run these commands in separate terminals:${NC}"
echo ""
echo -e "${YELLOW}Terminal 1 — Web API:${NC}"
echo "  uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo -e "${YELLOW}Terminal 2 — Workers:${NC}"
echo "  python3 << 'EOF'"
echo "import asyncio"
echo "from pathlib import Path"
echo "from commerce_platform.platform.config.loader import load"
echo "from commerce_platform.platform.store.db import Database"
echo "from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers"
echo "config = load(Path('config.yaml'))"
echo "db = Database(config.platform.store)"
echo "async def main():"
echo "    await db.open()"
echo "    try:"
echo "        await run_stock_and_deals_workers(config, 'config.yaml', db=db)"
echo "    finally:"
echo "        await db.close()"
echo "asyncio.run(main())"
echo "EOF"
echo ""
echo -e "${YELLOW}Terminal 3 — Browser:${NC}"
echo "  http://localhost:8000/deals"
echo ""

# Health check URLs
echo -e "${BLUE}Monitoring URLs (after startup):${NC}"
echo "  System Status:      http://localhost:8000/health/system"
echo "  Deals Status:       http://localhost:8000/health/deals"
echo "  Recent Deals:       http://localhost:8000/health/deals/recent"
echo "  Pending Approval:   http://localhost:8000/health/deals/pending-approval"
echo "  Public API:         http://localhost:8000/api/deals"
echo "  Deals Frontend:     http://localhost:8000/deals"
echo "  Admin Panel:        http://localhost:8000/admin"
echo ""

# Quick test
echo -e "${BLUE}Quick Verification:${NC}"
echo ""
echo -e "${YELLOW}1. Check if API will start:${NC}"
python3 -c "from commerce_platform.web.main import create_app; print('   ✓ FastAPI app can be imported')"

echo -e "${YELLOW}2. Check if workers can start:${NC}"
python3 -c "from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers; print('   ✓ Worker bootstrap can be imported')"

echo -e "${YELLOW}3. Check database schema:${NC}"
python3 << 'PYEOF'
import asyncio
from commerce_platform.platform.store.db import Database
from commerce_platform.platform.config.loader import load
from pathlib import Path

async def check():
    config = load(Path('config.yaml'))
    db = Database(config.platform.store)
    try:
        await db.open()
        print("   ✓ Database connection OK")
        await db.close()
    except Exception as e:
        print(f"   ✗ Database error: {e}")

asyncio.run(check())
PYEOF

echo ""
echo -e "${GREEN}==================================================================="
echo "  System Ready for Startup"
echo "===================================================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Start Terminal 1 (API) — wait for 'Application startup complete'"
echo "  2. Start Terminal 2 (Workers) — wait for 'discovery-loop started'"
echo "  3. Open http://localhost:8000/deals in your browser"
echo "  4. Monitor: http://localhost:8000/health/system"
echo ""
