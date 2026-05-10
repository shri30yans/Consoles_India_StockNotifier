# Complete End-to-End Deal Discovery Platform

## Quick Start

```bash
python verify_system.py

python -m commerce_platform --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/deals

**Advanced (two terminals):** run `uvicorn commerce_platform.web.main:app …` and `python scripts/workers.py` if you want hot-reload on the API while workers run separately.

## System Flow

1. **`StockRunner`** (`commerce_platform.stock.runner`) reloads merged config on an interval and schedules:
   - Per-product **`Poller`** jobs (stock watches)
   - Per-platform-source **`DealDiscoveryWatcher`** tasks for deal listing URLs

2. **`DealDiscoveryWatcher`** (`commerce_platform.stock.deal_discovery_watcher`)
   - Uses **`PlaywrightFetcher`**: **`get_html_rendered()`** for JS-heavy listings, **`get_html()`** for faster PDP fetches where applicable
   - Parses listings via **`commerce_platform.stock.sources.serp_parsers`** (multi-fallback: CSS → JSON-LD → **`ValueError`**)
   - Scores with **`DealScorer`**, **`DealRepo.upsert`** into **`deals`**, publishes **`PriceObservation`** to the in-process **`EventBus`**

3. **Observation pipeline** (`commerce_platform.runtime.worker_bootstrap`, task name **`observation-processor`**)
   - Subscribes to **`PriceObservation`**, persists stock/price snapshots, runs **`RuleEngine`**, sends notifications through **`NotificationHandler`** / **`ChannelRouter`** (`commerce_platform.platform.notify.*`)

**Parsers fail loud:** extraction errors raise **`ValueError`** and show up in logs immediately; live tests (e.g. **`tests/test_deal_scrapers_live.py`**) catch CSS drift.

## Key Features

✅ **Multi-fallback discovery parsing**: BS4 + JSON-LD where available; **`ValueError`** on failure  
✅ **Fail-loud diagnostics**: No automatic selector repair — fix parsers when retailers change HTML  
✅ **Admin approval**: Pending deals exposed via **`/api/system/deals/pending-approval`** and admin APIs  
✅ **Public API**: `/api/deals` with retailer & discount filters  
✅ **Affiliate links**: Channel layer can rewrite URLs via **`AffiliateRewriter`** / config  
✅ **Single process**: API + workers + **`EventBus`** in one Python interpreter today  
✅ **Observable**: Structured logging across runner, watcher, and observation pipeline  

## Testing

```bash
# Live retailer parsing (may fail when sites change — expected)
pytest tests/test_deal_scrapers_live.py -v

# View public deals API
curl http://localhost:8000/api/deals?retailer=amazon&min_discount=0.15

# Admin approves deal (JWT required)
curl -X POST http://localhost:8000/api/admin/deals/1/approve \
  -H "Authorization: Bearer TOKEN" \
  -d '{"note": "Great deal"}'
```

## Architecture

```
Frontend (React)
    ↓ HTTP
FastAPI (:8000) — static SPA + /api/*
    ↓ asyncpg
PostgreSQL — deals, config_settings, price_snapshots, …

Same process:
  StockRunner → Poller / DealDiscoveryWatcher
  observation-processor → EventBus(PriceObservation) → RuleEngine → notify (telegram, discord, twitter, …)

Repos: commerce_platform.platform.store.repos.*
Parsers: commerce_platform.stock.parsers.* ; listings: commerce_platform.stock.sources.serp_parsers
```

## Production Ready

- ✅ Type hints throughout
- ✅ Async/await patterns
- ✅ Error handling and logging
- ✅ Database migrations
- ✅ API authentication
- ✅ In-process event bus for observations
- ✅ Documentation aligned with single-process deployment

See AGENT_SYSTEM.md for historical diagrams (verify dates against code).
