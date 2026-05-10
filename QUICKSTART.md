# Quick Start — Deal Discovery Platform

Run **`python -m commerce_platform`** to start **FastAPI + stock/deals workers + observation pipeline** in **one process**. Use **two terminals** only if you want separate shells for logs vs curl.

## Prerequisites (Already Verified ✓)
- Python 3.10+: installed
- PostgreSQL: Supabase connection confirmed
- Config: `config.yaml` loaded with platform sources
- Database: Schema initialized (deals, config_settings, and required tables)

---

## 1. Initialize Database (One-Time)

```powershell
python scripts/init_db.py
```

**Output:**
```
Database schema initialized successfully!
```

---

## 2. Start the Platform (Single Command)

From the repo root (with `.env` loaded — `python -m commerce_platform` loads dotenv):

```powershell
python -m commerce_platform --host 0.0.0.0 --port 8000
```

This starts:
- HTTP API and static frontend on port **8000**
- **`StockRunner`** (`commerce_platform.stock.runner`) — schedules product polls and **`DealDiscoveryWatcher`** jobs from config
- **`observation-processor`** (`commerce_platform.runtime.worker_bootstrap`) — **`PriceObservation`** → **`RuleEngine`** → **`ChannelRouter`** / notifications

**Expected output (examples):**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO: StockRunner starting N jobs — full reload every …s
INFO: Registering amazon_deals discovery source: poll_every=…s min_discount=…%
INFO: DealDiscoveryWatcher started: type=amazon_deals seeds=… poll=…s
INFO: Rule matched: product=… rule=… retailer=…
```

**Verify:** Open http://localhost:8000/api/health → should include `"status": "ok"`

---

## 3. Optional: Workers Only (Debugging)

If you need the API in one terminal and workers in another (same DB):

**Terminal A — API only**
```powershell
uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal B — Workers**
```powershell
python scripts/workers.py
```

---

## 4. Monitor the System

### Live Deals API
```powershell
curl http://localhost:8000/api/deals?limit=10
```

### System Health Check
```powershell
curl http://localhost:8000/api/system
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
curl http://localhost:8000/api/system/deals/recent
```

### Pending Approval (Borderline / Unreviewed)
```powershell
curl http://localhost:8000/api/system/deals/pending-approval
```

### Watch Live Logs

Look for **`DealDiscoveryWatcher started`**, **`StockRunner starting`**, **`Registering … discovery source`**, **`Rule matched`**, or **`Error processing observation`** / parser tracebacks. Parser extraction failures surface as **`ValueError`** in logs; confirm with **`tests/test_deal_scrapers_live.py`** after retailer HTML changes.

### Check Database Directly
```powershell
SELECT retailer, COUNT(*) as count, ROUND(AVG(score), 2) as avg_score
FROM deals WHERE is_active = true
GROUP BY retailer
ORDER BY count DESC;
```

### Admin API (Approve/Reject Deals)
```powershell
curl "http://localhost:8000/api/system/deals/pending-approval"

curl -X POST "http://localhost:8000/api/admin/deals/DEAL_ID/approve" `
  -H "Authorization: Bearer JWT_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"note": "Good deal"}'
```

---

## 6. Verify Everything Works (Test Checklist)

- [ ] `python -m commerce_platform` runs without errors
- [ ] http://localhost:8000/api/health returns ok
- [ ] curl http://localhost:8000/api/system returns `overall_status` healthy (DB reachable)
- [ ] curl http://localhost:8000/api/deals returns an array (may be empty until first successful poll)
- [ ] Open http://localhost:8000/deals — grid loads
- [ ] Logs show `DealDiscoveryWatcher started` for enabled platform sources

---

## 7. Configuration

Base file: `config.yaml`. **Scoring threshold and weights** are overridden from the **`config_settings`** table (merged at runtime); edit via admin API or SQL.

### Deal Scoring Weights (in DB)
```sql
SELECT key, value FROM config_settings WHERE key LIKE 'deals.scoring.%';
```

Change via:
```
PATCH /api/admin/deals/config
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

---

## 8. Architecture at a Glance

```
python -m commerce_platform (one OS process)
    FastAPI :8000  ← React /deals, /api/*, /admin/*
         │
         └─ shared asyncpg pool ←→ PostgreSQL

asyncio.Tasks:
    StockRunner
      ├─ Poller (per product watch) → PriceObservation → EventBus
      └─ DealDiscoveryWatcher (per deal source) → parse/score → DealRepo

    observation-processor (in worker_bootstrap)
      EventBus (PriceObservation) → RuleEngine → NotificationHandler → ChannelRouter
      (telegram, discord, twitter, … — BaseHttpChannel for HTTP channels)
```

---

## 9. Stop the System

**Ctrl+C** in the terminal running `python -m commerce_platform`. Data persists in PostgreSQL.

---

## 10. Next Steps (Optional Enhancements)

- [ ] **Frontend Admin Tab**: Richer deals tab in AdminPage.tsx
- [ ] **Future / Not Built Yet:** **Hermes-style** adaptive discovery memory
- [ ] **Notifications**: Wire Telegram/Discord/X credentials in channel config
- [ ] **Future / Not Built Yet:** **Fraud / seller legitimacy** analyzer (no automatic selector repair exists today)
- [ ] **Future / Not Built Yet:** Retailer bot/CAPTCHA handling
- [ ] **Price Tracking**: Charts on product detail

---

**System Status: READY TO RUN** ✓

Run **`python -m commerce_platform`** and monitor **`http://localhost:8000/api/system`**.
