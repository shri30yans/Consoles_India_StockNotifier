# Deal Discovery Platform — Retail Scraping & Deal Feed

Deal discovery scrapes Amazon/Flipkart/Ajio/Myntra deal surfaces, scores deals against price history, and exposes an admin approval workflow. Parsers use multi-fallback extraction and fail loud when markup changes.

---

## Quick Start (5 Minutes)

```bash
# 1. Verify system is ready
python verify_system.py

# 2. Run API + workers in one process (FastAPI + asyncio tasks)
python -m commerce_platform --host 0.0.0.0 --port 8000

# 3. Open the app
open http://localhost:8000/deals
# or check health: curl http://localhost:8000/api/system
```

**First discovery runs after your configured poll intervals. Deals appear on `/deals` as they are scored and upserted.**

---

## What's Included

### Backend
- **`commerce_platform.stock.runner.StockRunner`**: Loads config on a reload timer, schedules per-product stock polls and per-source deal discovery jobs as asyncio tasks.
- **`commerce_platform.stock.deal_discovery_watcher.DealDiscoveryWatcher`**: Fetches listing pages (rendered path where needed), parses items via `commerce_platform.stock.sources.serp_parsers` (CSS → JSON-LD → `ValueError`), scores with `DealScorer`, upserts into `deals`.
- **`commerce_platform.runtime.worker_bootstrap`**: Starts `stock-runner` and `observation-processor` tasks — the latter subscribes to the in-process **`EventBus`** for **`PriceObservation`**, persists snapshots, runs **`RuleEngine`**, and dispatches notifications through **`ChannelRouter`** / **`NotificationHandler`** (`commerce_platform.platform.notify.*`, HTTP plumbing via **`BaseHttpChannel`**).
- **`PlaywrightFetcher`**: One fetcher with **`get_html()`** (fast) and **`get_html_rendered()`** for JS-heavy listings.

### Frontend
- **DealsPage** (`/deals`): Public deal grid with filters and auto-refresh
- **AdminPage** (`/admin`): Dashboard for config + deal approval (API-backed)

### Database
- **PostgreSQL** (e.g. Supabase): Deals, catalog, price history, user rules — via **`asyncpg`**
- **Runtime tunables**: Scoring threshold and weights in **`config_settings`**, editable through the admin API (no restart)

### APIs
- `GET /api/deals` — Public deals API with filtering
- `GET /api/system` — Real-time system health checks
- `PATCH /api/admin/deals/config` — Update scoring config
- `POST /api/admin/deals/{id}/approve` — Approve/reject deals

---

## Documentation

| Doc | Purpose |
|-----|---------|
| **[QUICKSTART.md](QUICKSTART.md)** | Startup guide with expected outputs |
| **[SYSTEM_READY.md](SYSTEM_READY.md)** | Complete system overview |
| **[MONITORING.md](MONITORING.md)** | Troubleshooting (SQL, logs, common issues) |
| **[frontend/COMPLETE_SETUP.md](frontend/COMPLETE_SETUP.md)** | End-to-end setup notes |
| **[AGENT_SYSTEM.md](AGENT_SYSTEM.md)** | Architecture notes (verify against code if older) |
| **[CLAUDE.md](CLAUDE.md)** | Implementation principles |

---

## First Run Expected Behavior

Timing depends on `config.yaml` (`poll_seconds`, `config_reload_seconds`, etc.).

```
T=0s      python -m commerce_platform binds HTTP (default port 8000)
T= soon   StockRunner builds jobs from config; DealDiscoveryWatcher logs seed URLs and poll interval
T= …      Listing parse → PDP parse → score → DealRepo.upsert; PriceObservation events → observation-processor
```

**Check results:**
```bash
curl http://localhost:8000/api/deals?limit=10

curl http://localhost:8000/api/system/deals/pending-approval
```

---

## Architecture at a Glance

```
Single process (python -m commerce_platform)
  FastAPI (:8000)
    ├─ Static: React DealsPage
    ├─ /api/deals, /api/system, /admin/*  → same DB pool as workers

  asyncio.Tasks
    ├─ StockRunner → per-watch Poller jobs + platform DealDiscoveryWatcher loops
    ├─ observation-processor → EventBus (PriceObservation) → RuleEngine → ChannelRouter / notifications

  PlaywrightFetcher → listing (rendered) + PDP (fast path)

PostgreSQL
  ├─ deals (upsert semantics)
  ├─ config_settings (scoring, affiliates, …)
  ├─ price_snapshots / catalog / rules / …
```

**Design:** One Python process today — API, scraping workers, and notification pipeline share memory (including one **`EventBus`** instance). No Redis, no IPC, no microservices at current scale.

---

## Key Design Decisions

### 1. Multi-Fallback Parsing
- Try CSS selectors (fast, brittle)
- Fall back to JSON-LD where available
- Raise **`ValueError`** on failure (fail loud, never silent)
- **Live tests** (e.g. `tests/test_deal_scrapers_live.py`) catch retailer CSS drift; fix selectors in code when extraction fails

### 2. In-Process Events
- **`PriceObservation`** flows on the **`EventBus`**; **`observation-processor`** evaluates rules and routes to Telegram / Discord / X / HTTP channels

### 3. Upsert Semantics (Not Append-Only)
One row per product URL with state machine:
- `inserted` → new deal found
- `confirmed` → same price, still live
- `price_improved` → price dropped
- `reactivated` → was expired, came back
- `expired` → price rose or out-of-stock

Result: Deals table is a clean snapshot, not a noisy audit log.

### 4. Consolidation-First Code
- One method with parameters instead of many similar methods
- Single canonical row converter in repos
- `mark_reviewed(status: Literal["approved", "rejected"])` — see [CLAUDE.md](CLAUDE.md)

---

## Configuration

Base config: `config.yaml`. **Runtime tunables** (scoring threshold, weights) live in **`config_settings`** and override YAML via merged config.

### Scoring Weights (Default)
```json
{
  "lowest_90d": 0.35,
  "below_30d_median": 0.30,
  "discount_vs_mrp": 0.20,
  "cross_retailer_best": 0.15
}
```

Change via:
```bash
curl -X PATCH http://localhost:8000/api/admin/deals/config \
  -H "Authorization: Bearer JWT_TOKEN" \
  -d '{"threshold": 0.35, "weights": {...}}'
```

### Affiliate Tags (per Retailer)
```sql
UPDATE config_settings
SET value = '{"tag": "consolesind09-21", "param_name": "tag"}'
WHERE key = 'affiliate.amazon';
```

All URLs served via `/api/deals` can be rewritten with affiliate tags per channel configuration.

---

## Monitoring & Troubleshooting

### System Health
```bash
curl http://localhost:8000/api/system | jq '.checks'
```

### Recent Discoveries
```bash
curl http://localhost:8000/api/system/deals/recent | jq '.deals[0]'
```

### Pending Admin Review
```bash
curl http://localhost:8000/api/system/deals/pending-approval | jq '.deals | length'
```

### Logs & Parser Failures
Watch application logs for extraction **`ValueError`**s and stack traces from listing/PDP parsers. Run live scraper tests after retailer HTML changes.

See [MONITORING.md](MONITORING.md) for the full troubleshooting guide.

---

## Next Steps (Optional Enhancements)

- [ ] **Admin Deals UI Tab**: Richer UI for approvals beyond API-only flows
- [ ] **Future / Not Built Yet:** **Hermes Integration** — persistent agent memory across sessions
- [ ] **Future / Not Built Yet:** **FraudDetectionAgent** — seller rating / policy signals
- [ ] **Future / Not Built Yet:** **WebIntelligenceAgent** — CAPTCHA / bot handling
- [ ] **Price Charts**: Historical price visualization per product

---

## Deployment

**Local development**
```bash
python verify_system.py
python -m commerce_platform --host 0.0.0.0 --port 8000
```

**Cloud (typical)**
- Database: managed PostgreSQL (`DATABASE_URL` / platform store DSN)
- App: single container or VM running `python -m commerce_platform`
- Frontend: static assets served by the same FastAPI app from `commerce_platform/web/static`

---

## Questions?

1. **How do I get started?** → [QUICKSTART.md](QUICKSTART.md)
2. **How does the system work?** → [SYSTEM_READY.md](SYSTEM_READY.md)
3. **Parser broke, what now?** → Fix selectors / JSON-LD paths in `commerce_platform.stock.parsers` and `commerce_platform.stock.sources.serp_parsers`; confirm with `tests/test_deal_scrapers_live.py`
4. **How do I add a new retailer?** → Add parser under `commerce_platform/stock/parsers/`, listing extraction as needed in `serp_parsers`, register the source in config
5. **How do I change scoring?** → Admin API or direct SQL on `config_settings` (see Configuration above)

---

**Single process, explicit failures, Postgres as source of truth — scale-up later is a deployment concern, not a premature split.**
