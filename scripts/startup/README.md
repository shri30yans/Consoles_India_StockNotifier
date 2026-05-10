# Startup Guide — Deal Discovery Platform

## Quick Start (30 Seconds)

### Windows
```bash
scripts/startup.bat
```

### Linux / Mac
```bash
bash scripts/startup.sh
```

This opens **2 terminal windows** and shows you what to do next.

---

## What Gets Started

**Terminal 1: API Server** (port 8000)
- Serves the React frontend
- Serves the REST API (`/api/deals`, `/api/health`, `/api/system`, etc.)
- Auto-reloads on code changes (when launched via the script’s uvicorn mode — see repo scripts)

**Terminal 2: Workers** (when using split layout)
- **`StockRunner`** schedules stock polls and **`DealDiscoveryWatcher`** loops from `config.yaml`
- **`observation-processor`** consumes **`PriceObservation`** events from the in-process **`EventBus`** and routes notifications

Or run **everything in one shell**: `python -m commerce_platform --host 0.0.0.0 --port 8000` (API + workers together).

---

## Timeline

| Time | What Happens |
|------|--------------|
| T=0s | Process binds HTTP; worker tasks start |
| T= soon | **`StockRunner`** logs job count; **`DealDiscoveryWatcher`** logs `type=… seeds=… poll=…s` per enabled source |
| T= … | First successful poll upserts deals; **`Rule matched`** may appear when rules fire |

Poll intervals come from **`config.yaml`** (`poll_seconds` per source — not fixed “60 min” globally).

---

## Next Steps After Startup

1. **Open browser:**
   ```
   http://localhost:8000/deals
   ```

2. **Wait for the configured poll interval** for first listing scrape

3. **Deals appear** on the grid as **`DealRepo.upsert`** succeeds

4. **Auto-refreshes** every 90 seconds (frontend)

---

## Check Health

```bash
curl http://localhost:8000/api/health

curl http://localhost:8000/api/system

http://localhost:8000/deals
```

---

## Stop the System

In each terminal window, press **Ctrl+C** to stop.

---

## Manual Startup (If Scripts Don't Work)

**One process (recommended):**
```bash
python -m commerce_platform --host 0.0.0.0 --port 8000
```

**Split (optional):**

**Terminal 1:**
```bash
python scripts/api_server.py
```

**Terminal 2:**
```bash
python scripts/workers.py
```

Then open browser to `http://localhost:8000/deals`

---

## Troubleshooting

### Port 8000 already in use
```bash
# macOS/Linux
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### System verification fails
```bash
python verify_system.py
```

Shows exactly what's missing (Python packages, database, etc.)

### No deals after polls
Check worker logs for **`Deal discovery poll error`**, **`ValueError`** from parsers, or DB errors. Parser extraction failures are explicit — update **`commerce_platform.stock.sources.serp_parsers`** / PDP parsers and re-run **`tests/test_deal_scrapers_live.py`**.

### Observation / notification issues
Look for **`Error processing observation`** or channel errors in logs; verify channel credentials and **`commerce_platform.platform.notify`** configuration.

### Database or repository errors
If responses from `/api/system` show database/deals/stock errors, check:
```bash
curl http://localhost:8000/api/system
```

If database shows `"error"`, run:
```bash
python verify_system.py
```

---

## Architecture

```
Port 8000 (FastAPI)
├─ React frontend (http://localhost:8000/deals)
├─ REST API (/api/deals, /api/health, /api/system, …)
└─ Shared Postgres pool with worker tasks

Same Python process (typical: python -m commerce_platform)
├─ StockRunner — Poller jobs + DealDiscoveryWatcher (deal sources)
├─ observation-processor — EventBus → RuleEngine → ChannelRouter / NotificationHandler
└─ PlaywrightFetcher — get_html / get_html_rendered
```

---

## For More Info

- [../../QUICKSTART.md](../../QUICKSTART.md) — Detailed startup guide
- [../../MONITORING.md](../../MONITORING.md) — Health checks & troubleshooting
- [../../README.md](../../README.md) — Architecture overview
