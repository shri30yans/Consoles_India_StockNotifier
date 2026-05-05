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
- Serves the REST API (`/api/deals`, `/api/health`, etc.)
- Auto-reloads on code changes

**Terminal 2: Workers**
- Polls retailers every 60 minutes
- Scores deals against 90-day history
- Approves/rejects deals
- Auto-fixes broken parsers

---

## Timeline

| Time | What Happens |
|------|--------------|
| T=0s | Terminals open, API starts |
| T=30s | API responding, workers started |
| T=60s | **First discovery runs** — deals appear on page |
| T=120s | Curation loop approves/rejects deals |
| T=300s+ | Curation runs every 5 min, discovery every 60 min |

---

## Next Steps After Startup

1. **Open browser:**
   ```
   http://localhost:8000/deals
   ```

2. **Wait 60 seconds** for first deal discovery

3. **Deals appear** on the grid automatically

4. **Auto-refreshes** every 90 seconds

---

## Check Health

```bash
# Basic health
curl http://localhost:8000/api/health

# System status
curl http://localhost:8000/api/system

# Deals grid
http://localhost:8000/deals
```

---

## Stop the System

In each terminal window, press **Ctrl+C** to stop.

---

## Manual Startup (If Scripts Don't Work)

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

### No deals appear after 60 seconds
Check Terminal 2 logs for errors. Common issues:
- Database not connected
- Parser selectors broke (watch for "ParserFixerAgent analyzing...")
- Network issues (retailer websites down)

### "Curation pass failed"
Usually means deal_repo or config_repo error. Check:
```bash
curl http://localhost:8000/api/system
```

If database shows "error", run:
```bash
python verify_system.py
```

---

## Architecture

```
Port 8000 (API Server)
├─ Serves React frontend (http://localhost:8000/deals)
├─ Serves REST API (/api/deals, /api/health, etc.)
└─ Manages database connections

Workers (Async Tasks)
├─ StockRunner (product tracking)
├─ DiscoveryLoop (polls retailers every 60 min)
├─ CurationLoop (approves/rejects every 5 min)
├─ ParserFixerAgent (auto-fixes selectors)
└─ ObservationProcessor (notifications)
```

---

## For More Info

- [../../QUICKSTART.md](../../QUICKSTART.md) — Detailed 10-step guide
- [../../MONITORING.md](../../MONITORING.md) — Health checks & troubleshooting
- [../../README.md](../../README.md) — Architecture overview
