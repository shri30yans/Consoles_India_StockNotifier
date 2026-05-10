# Quick Start — Deal Discovery Platform

System verified and ready. Three terminals required to run the full pipeline.

## Prerequisites (Already Verified ✓)
- Python 3.10+: installed
- PostgreSQL: Supabase connection confirmed
- Config: `config.yaml` loaded with 5 platform sources
- Database: Schema initialized (deals, config_settings, and all required tables)

---

## 1. Initialize Database (One-Time)

```powershell
python scripts/init_db.py
```

Creates all tables (catalog_products, deals, config_settings, price_snapshots, stock_state, rules, etc.).

**Output:**
```
Database schema initialized successfully!
```

---

## 2. Terminal 1: Start the API Server

```powershell
uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Verify:** Open http://localhost:8000/health in browser → should return `{"status": "ok", ...}`

---

## 3. Terminal 2: Start the Workers

Workers poll retailers for deals, curate low-scoring deals, and auto-fix broken parsers.

```powershell
python -c "
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers

# Load environment
load_dotenv(Path('.env'), override=True)

# Run workers
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

**Expected output:**
```
INFO: stock-runner started (will reload config every 15s)
INFO: observation-processor started
INFO: discovery-loop started (polling every 3600s)
INFO: curation-loop started (reviewing every 300s)
INFO: parser-fixer started (listening for failures)
```

---

## 4. Terminal 3: Monitor the System

### Live Deals API
```powershell
curl http://localhost:8000/api/deals?limit=10
```

### System Health Check
```powershell
curl http://localhost:8000/health/system
```

Returns:
```json
{
  "overall_status": "healthy",
  "checks": {
    "database": { "status": "healthy" },
    "deals": { "active_deals": 42, "pending_approval": 3, "by_retailer": {...} },
    "stock": { "status": "healthy" },
    "api": { "status": "healthy" }
  }
}
```

### View Deals Frontend
```
http://localhost:8000/deals
```

Auto-refreshes every 90 seconds. Shows:
- Active deals from all retailers
- Score bar (90-day low, cross-retailer best, etc.)
- "Buy" button with affiliate tag
- Filter by retailer / min discount

---

## 5. Debug & Troubleshoot

### Recent Discoveries
```powershell
curl http://localhost:8000/health/deals/recent
```

Shows last 20 discovered deals with scores and reasons.

### Pending Approval (Borderline Deals)
```powershell
curl http://localhost:8000/health/deals/pending-approval
```

Deals scoring 0.30–0.40 (below auto-approve threshold) awaiting admin review.

### Watch Live Logs
```powershell
# Terminal 1: API logs (already visible)
# Terminal 2: Worker logs (already visible)
```

Look for:
```
INFO: Discovery: amazon_deals — found=47 qualified=12 created=3 updated=2
INFO: Curation: pending=3 sent_to_admin=2 approved=1
INFO: ParserFixerAgent analyzing failure for flipkart_deals
INFO: Claude suggested selectors: {".dealContainer": ".DealCard-module__dealContent"}
```

### Check Database Directly
```powershell
# Open psql or DBeaver connected to your Supabase database
# Then query:

SELECT retailer, COUNT(*) as count, ROUND(AVG(score), 2) as avg_score
FROM deals WHERE is_active = true
GROUP BY retailer
ORDER BY count DESC;
```

### Admin API (Approve/Reject Deals)
```powershell
# Get a pending deal ID
curl "http://localhost:8000/health/deals/pending-approval" | ConvertFrom-Json | select -ExpandProperty deals | select id, title | head -1

# Approve it (replace DEAL_ID with actual ID, and JWT_TOKEN from auth)
curl -X POST "http://localhost:8000/api/admin/deals/DEAL_ID/approve" `
  -H "Authorization: Bearer JWT_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"note": "Good deal"}'
```

---

## 6. Verify Everything Works (Test Checklist)

- [ ] Terminal 1: API is running and responsive
- [ ] Terminal 2: Workers are running (5 loops started)
- [ ] Terminal 3: curl http://localhost:8000/health/system returns overall_status: "healthy"
- [ ] Terminal 3: curl http://localhost:8000/api/deals returns array of deals
- [ ] Terminal 3: Open http://localhost:8000/deals in browser, see deal grid
- [ ] Check logs: "Discovery: amazon_deals — found=..." appears in worker logs within 60 sec
- [ ] Wait 60 sec for discovery to run, then refresh /api/deals and browser

---

## 7. Configuration

All config is in `config.yaml` + `config_settings` database table.

### Deal Scoring Weights (in DB)
```sql
SELECT key, value FROM config_settings WHERE key LIKE 'deals.scoring.%';
```

Change via:
```
PATCH /admin/deals/config
{
  "threshold": 0.40,
  "weights": {
    "lowest_90d": 0.35,
    "below_30d_median": 0.30,
    "discount_vs_mrp": 0.20,
    "cross_retailer_best": 0.15
  }
}
```

### Affiliate Tags (per retailer)
```sql
SELECT key, value FROM config_settings WHERE key LIKE 'affiliate.%';
```

Change via:
```
PATCH /admin/affiliate/config
[
  {"retailer": "amazon", "tag": "consolesind09-21", "param_name": "tag"},
  {"retailer": "flipkart", "tag": "aff_1234", "param_name": "affid"}
]
```

---

## 8. Architecture at a Glance

```
Terminal 1 (API Port 8000)
    ↓
    FastAPI ← serves /deals UI, /api/deals, /health/*, /admin/*
    ↓
    PostgreSQL (Supabase)

Terminal 2 (Workers)
    ↓
    DiscoveryLoop (every 60 min) → scrapes amazon/flipkart/ajio/myntra
    ↓ (finds deals)
    DealRepo.upsert() → deals table
    ↓
    CurationLoop (every 5 min) → reviews pending deals
    ↓ (score < 0.40)
    Sends to /api/admin/deals for approval
    ↓
    ParserFixerAgent (listens for failures)
    ↓ (parser broke)
    Calls Claude to analyze HTML + suggest new CSS selectors
    ↓
    Next poll cycle uses new selectors ✓
```

---

## 9. Stop the System

```
Terminal 1: Ctrl+C (FastAPI)
Terminal 2: Ctrl+C (Workers)
Terminal 3: Ctrl+C (Monitor/Curl)
```

Data persists in PostgreSQL. Next run will continue from last state.

---

## 10. Next Steps (Optional Enhancements)

- [ ] **Frontend Admin Tab**: Build Deals tab in AdminPage.tsx (currently available via API only)
- [ ] **Hermes Agent Integration**: Fork Hermes repo and integrate for adaptive discovery
- [ ] **Notifications**: Set up Telegram/Discord for new deal alerts
- [ ] **Fraud Detection**: Add ParserFixerAgent-style analyzer for seller legitimacy
- [ ] **Web Intelligence**: Add agent to handle CAPTCHA, bot detection on retailers
- [ ] **Price Tracking**: Build price history visualization on product detail page

---

**System Status: READY TO RUN** ✓

Start the three terminals above and monitor http://localhost:8000/health/system
