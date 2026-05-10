# Deal Discovery Platform — AI-Native Retail Scraping

Autonomous deal discovery engine that scrapes Amazon/Flipkart/Ajio/Myntra deal pages, scores deals against 90-day price history, and curates via admin approval workflow. Agents adapt when HTML parsers break.

---

## Quick Start (5 Minutes)

```bash
# 1. Verify system is ready
python verify_system.py

# 2. Terminal 1 — API Server
uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Terminal 2 — Workers (discovery, curation, parser fixing)
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

# 4. Terminal 3 — Monitor
open http://localhost:8000/deals
# or check health: curl http://localhost:8000/health/system
```

**First discovery runs in ~60 seconds. See deals appear on your feed!**

---

## What's Included

### Backend
- **DealDiscoveryAgent**: Autonomous deal scraping (Amazon, Flipkart, Ajio, Myntra)
- **CuratorAgent**: Auto-approves high-confidence deals, routes low-confidence to admin
- **ParserFixerAgent**: Detects HTML parsing failures, calls Claude to suggest new CSS selectors
- **EventBus**: Loose coupling between discovery, curation, and notifications

### Frontend
- **DealsPage** (`/deals`): Public deal grid with filters and auto-refresh
- **AdminPage** (`/admin`): Dashboard for config + deal approval (API-only for now)

### Database
- **PostgreSQL** (Supabase): Deals, catalog, price history, user rules
- **Config as Code**: Scoring weights, affiliate tags, sources — all editable via API or DB

### APIs
- `GET /api/deals` — Public deals API with filtering
- `GET /health/system` — Real-time system health checks
- `POST /api/deals/discover` — Agent gateway for discovery reports
- `PATCH /admin/deals/config` — Update scoring config
- `POST /api/admin/deals/{id}/approve` — Approve/reject deals

---

## Documentation

| Doc | Purpose |
|-----|---------|
| **[QUICKSTART.md](QUICKSTART.md)** | 10-step startup guide with expected outputs |
| **[SYSTEM_READY.md](SYSTEM_READY.md)** | Complete system overview (what was built + how it works) |
| **[MONITORING.md](MONITORING.md)** | Troubleshooting guide (SQL queries, live logs, common issues) |
| **[COMPLETE_SETUP.md](COMPLETE_SETUP.md)** | Comprehensive setup with test cases |
| **[AGENT_SYSTEM.md](AGENT_SYSTEM.md)** | Agent architecture + event flow diagrams |
| **[CLAUDE.md](CLAUDE.md)** | Implementation principles (consolidation-first, type safety, etc.) |

---

## First Run Expected Behavior

```
T=0s      API server starts (port 8000)
T=5s      Workers initialize
T=10-60s  DiscoveryLoop polls amazon.in/deals
          Extracts 50 items, pre-filters to 32, scores vs history
          Upserts 12 deals to database
T=65s     CurationLoop reviews pending deals
          Scores >= 0.40 → auto-approved (9 deals)
          Scores < 0.40 → pending admin review (3 deals)
T=300s    Next curation pass (every 5 min)
T=3600s   Next discovery pass (every 60 min)
```

**Check results:**
```bash
curl http://localhost:8000/api/deals?limit=10
# Should return 9 approved deals

curl http://localhost:8000/health/deals/pending-approval
# Should return 3 deals awaiting admin review
```

---

## Architecture at a Glance

```
FastAPI (Port 8000)
  ├─ Static files: React DealsPage UI
  ├─ /api/deals: Public deal browsing
  ├─ /health/*: System monitoring
  └─ /admin/*: Configuration + approvals

PostgreSQL (Supabase)
  ├─ deals: Discovered good deals (upsert semantics)
  ├─ config_settings: Admin-editable config (JSON)
  ├─ price_snapshots: 90-day price history
  └─ [Other tables: catalog, users, rules, etc.]

Workers (Async Tasks)
  ├─ StockRunner: Product availability tracking
  ├─ DiscoveryLoop: Retail page scraping (every 60 min)
  ├─ CurationLoop: Deal approval (every 5 min)
  ├─ ParserFixerAgent: CSS selector repair (on-demand)
  └─ ObservationProcessor: Price notifications
```

---

## Key Design Decisions

### 1. Multi-Fallback Parsing
- Try CSS selectors (fast, brittle)
- Fall back to JSON-LD (slower, reliable)
- Raise ValueError (fail loud, never silent)
- ParserFixerAgent auto-fixes next cycle

### 2. Autonomous Agents
- Event-driven coordination (no tight coupling)
- Agents run independently, publish results
- Easy to add new agents (fraud detection, web intelligence, etc.)

### 3. Upsert Semantics (Not Append-Only)
One row per product URL with state machine:
- `inserted` → new deal found
- `confirmed` → same price, still live
- `price_improved` → price dropped
- `reactivated` → was expired, came back
- `expired` → price rose or out-of-stock

Result: Deals table is always a clean snapshot, not a noisy audit log.

### 4. Consolidation-First Code
- One method with parameters instead of many similar methods
- Single canonical converter for all database queries
- `mark_reviewed(status: Literal["approved", "rejected"])` not `approve()` + `reject()`
- See [CLAUDE.md](CLAUDE.md) for full principles

---

## Configuration

All config lives in `config.yaml` + `config_settings` database table.

### Scoring Weights (Default)
```json
{
  "lowest_90d": 0.35,           // Is this 90-day low?
  "below_30d_median": 0.30,     // Below 30-day median?
  "discount_vs_mrp": 0.20,      // Discount vs displayed MRP
  "cross_retailer_best": 0.15   // Best price across retailers
}
```

Change via:
```bash
curl -X PATCH http://localhost:8000/admin/deals/config \
  -H "Authorization: Bearer JWT_TOKEN" \
  -d '{"threshold": 0.35, "weights": {...}}'
```

### Affiliate Tags (per Retailer)
```sql
UPDATE config_settings
SET value = '{"tag": "consolesind09-21", "param_name": "tag"}'
WHERE key = 'affiliate.amazon';
```

All URLs served via `/api/deals` are automatically rewritten with affiliate tags.

---

## Monitoring & Troubleshooting

### System Health
```bash
curl http://localhost:8000/health/system | jq '.checks'
```

### Recent Discoveries
```bash
curl http://localhost:8000/health/deals/recent | jq '.deals[0]'
```

### Pending Admin Review
```bash
curl http://localhost:8000/health/deals/pending-approval | jq '.deals | length'
```

### Database Queries
```sql
-- Deal stats by retailer
SELECT retailer, COUNT(*) as total, ROUND(AVG(score), 2) as avg
FROM deals WHERE is_active = true GROUP BY retailer;

-- Parser errors (watched by ParserFixerAgent)
SELECT key, value->>'error' FROM config_settings
WHERE key LIKE 'parser.error.%';
```

See [MONITORING.md](MONITORING.md) for complete troubleshooting guide.

---

## Next Steps (Optional Enhancements)

- [ ] **Admin Deals UI Tab**: Build UI for approvals (currently API-only)
- [ ] **Hermes Integration**: Persistent agent memory across sessions
- [ ] **FraudDetectionAgent**: Analyze seller rating, reviews, return policy
- [ ] **WebIntelligenceAgent**: Handle CAPTCHA, bot detection
- [ ] **Notifications**: Telegram/Discord/SMS for new deals
- [ ] **Price Charts**: Historical price visualization per product

---

## Deployment

**Local Development** (what you're doing):
```bash
python verify_system.py  # Pre-flight check
# Then run 3 terminals (see QUICKSTART.md)
```

**Cloud** (production):
- Database: Supabase PostgreSQL (already configured via `DATABASE_URL`)
- API: Cloud Run, Lambda, or self-hosted
- Workers: Cloud Functions, Cloud Tasks, or self-hosted
- Frontend: Static CDN (React build output)

---

## Questions?

1. **How do I get started?** → Read [QUICKSTART.md](QUICKSTART.md)
2. **How does the system work?** → Read [SYSTEM_READY.md](SYSTEM_READY.md)
3. **Parser broke, what now?** → Read [MONITORING.md](MONITORING.md)
4. **How do I add a new retailer?** → See `commerce_platform/stock/parsers/` + add parser + register in config
5. **How do I change scoring?** → Use API or SQL (see Configuration section above)

---

**Built with autonomy in mind. Agents adapt. Parsers self-heal. You stay informed.**
