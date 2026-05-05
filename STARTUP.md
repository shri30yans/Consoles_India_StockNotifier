# Startup Guide — Deal Discovery Platform

**Two ways to start the system:**

## Option 1: Automated Startup (Easiest)

### Windows
```powershell
# Double-click this file:
start.bat
```

**What happens:**
1. System verification runs
2. Three cmd windows open automatically
3. Browser opens to http://localhost:8000/deals
4. Deals appear on page within 60 seconds

### Linux / Mac
```bash
bash start.sh
```

**What happens:**
1. System verification runs
2. Three terminal windows open automatically
3. Browser opens to http://localhost:8000/deals
4. Health checks run every 30 seconds

---

## Option 2: Manual Startup (Full Control)

Open **three separate terminal windows** and run each command:

### Terminal 1: API Server
```bash
cd C:\Programs\Consoles_India_StockNotifier
uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2: Workers
```bash
cd C:\Programs\Consoles_India_StockNotifier
python -c "
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
"
```

Expected output:
```
INFO: stock-runner started (will reload config every 15s)
INFO: observation-processor started
INFO: discovery-loop started (polling every 3600s)
INFO: curation-loop started (reviewing every 300s)
INFO: parser-fixer started (listening for failures)
```

### Terminal 3: Monitor
Open in browser:
```
http://localhost:8000/deals
```

Or check health:
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/system
```

---

## What Happens Next

### T=0s (Startup)
- API server starts on port 8000
- Workers initialize (5 async tasks)
- Frontend loads at http://localhost:8000/deals

### T=0-30s
- Deal discovery waits for first poll
- Deals page shows "Loading..."
- Health checks respond with empty data

### T=60s (First Discovery)
- DiscoveryLoop polls Amazon/Flipkart/Ajio/Myntra
- Extracts 50+ items from deal pages
- Pre-filters by minimum 15% discount
- Scores against 90-day price history
- Upserts 5-15 deals to database

**Deals now appear on the page!**

### T=120s
- CurationLoop reviews new deals
- Auto-approves high-confidence (score ≥ 0.40)
- Routes low-confidence to admin for review

### T=300s+
- Curation loop runs every 5 minutes
- Discovery loop runs every 60 minutes
- Parser fixer listens for failures

---

## Health Check URLs

Once the system is running:

| URL | Purpose | Expected Response |
|-----|---------|-------------------|
| `http://localhost:8000/api/health` | Basic health | `{"status":"ok","timestamp":"..."}` |
| `http://localhost:8000/api/system` | Full system status | `{"overall_status":"healthy","checks":{...}}` |
| `http://localhost:8000/deals` | Public deals page | Deal grid (empty at first, populates in 60s) |

### Example Health Check
```bash
curl http://localhost:8000/api/system | jq '.checks'
```

Output:
```json
{
  "database": {
    "status": "healthy",
    "message": "PostgreSQL connection OK"
  },
  "deals": {
    "status": "healthy",
    "active_deals": 12,
    "pending_approval": 2,
    "by_retailer": {
      "amazon": 4,
      "flipkart": 5,
      "ajio": 2,
      "myntra": 1
    }
  },
  "stock": { "status": "healthy" },
  "api": { "status": "healthy" }
}
```

---

## Stopping the System

### Option 1 (Automated Startup)
Close each terminal window (Ctrl+C in each, or just close the window)

### Option 2 (Manual Startup)
In each terminal, press **Ctrl+C**

The system will:
1. Stop accepting new requests
2. Close database connections
3. Exit gracefully

---

## Common Startup Issues

### "Port 8000 already in use"
```bash
# Find process using port 8000
lsof -i :8000        # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill it (replace PID)
kill <PID>           # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### "Database connection failed"
- Check `.env` file exists
- Verify `DATABASE_URL` is set: `echo $DATABASE_URL`
- Check PostgreSQL/Supabase is accessible
- Run verification: `python verify_system.py`

### "Deals not appearing after 60s"
1. Check Terminal 2 logs for discovery errors
2. Check API logs (Terminal 1) for 500 errors
3. Check database connection: `python verify_system.py`
4. Try manual health check: `curl http://localhost:8000/api/system`

### "Verification script fails"
```bash
python verify_system.py
```

This will tell you exactly what's missing (Python packages, database, config, etc.)

---

## Configuration

All config is in one place: **config.yaml**

Key settings:
- `platform_sources`: Which retailers to scrape
- `deals.scoring.threshold`: Auto-approve score (default 0.40)
- `channels`: Where to send notifications (Telegram, Discord, etc.)

Change config, then restart Terminal 2 (workers) to pick up changes.

---

## Next Steps

1. **Verify startup works:** Run the startup script once
2. **Monitor first discovery:** Watch Terminal 2 logs and deals page
3. **Check health:** Run health checks to understand system state
4. **Customize:** Edit `config.yaml` to add retailers, change thresholds, etc.
5. **Integrate notifications:** Set up Telegram/Discord in `config.yaml`

For detailed info, see:
- [QUICKSTART.md](QUICKSTART.md) — 10-step guide
- [MONITORING.md](MONITORING.md) — Health checks & troubleshooting
- [SYSTEM_READY.md](SYSTEM_READY.md) — Architecture overview
- [README.md](README.md) — Quick reference

---

## Architecture at a Glance

```
Terminal 1 (API)
  FastAPI on :8000
  ├─ /deals → React frontend
  ├─ /api/deals → JSON API
  └─ /api/health → Status checks

Terminal 2 (Workers)
  Async tasks
  ├─ StockRunner (product tracking)
  ├─ DiscoveryLoop (polls retailers)
  ├─ CurationLoop (approves/rejects)
  ├─ ParserFixerAgent (auto-fix selectors)
  └─ ObservationProcessor (notifications)

Terminal 3 (Monitor)
  Browser + curl health checks
  └─ Dashboard at http://localhost:8000/deals
```

All three run independently. You can restart one without restarting others.

---

**Ready to start? Run the startup script!**
