# Complete End-to-End Deal Discovery Platform — Setup & Operation

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Frontend (React/TypeScript)             │
│  /deals       → DealsPage (public deal grid)           │
│  /admin       → AdminPage (admin config)               │
│  /catalog     → CatalogPage (product catalog)          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│           FastAPI Backend (Port 8000)                   │
│  /api/deals/discover        ← Agent reports deals      │
│  /api/deals/parser-error    ← Agent reports failures   │
│  /api/deals/alert           ← Agent reports fraud      │
│  /api/products              → Public API               │
│  /api/admin/...             → Admin API (auth required)│
└────────────────┬──────────────────────────────┬────────┘
                 │                              │
        Database │                              │ EventBus
        (Postgres)                              │
                                     ┌──────────▼──────────┐
                                     │ Workers (Async)     │
                                     │                     │
                                     │ • StockRunner       │
                                     │ • DiscoveryLoop     │
                                     │ • CurationLoop      │
                                     │ • ParserFixerAgent  │
                                     │ • RuleEngine        │
                                     └─────────────────────┘

Discovery Flow:
───────────────
1. DiscoveryLoop polls Amazon/Flipkart/Ajio/Myntra every 60 min
2. Extracts ListingItems via BS4 + JSON-LD fallback
3. Pre-filters by minimum_discount_pct
4. Scores using DealScorer (vs 90d price history + MRP discount)
5. Upserts to deals table (one row per URL)
6. Publishes PriceObservation events
7. Reports via POST /api/deals/discover

Curation Flow:
──────────────
1. CuratorAgent checks deals pending approval (created in last 5 min)
2. Evaluates score vs threshold (0.40)
3. score ≥ 0.40 → auto-approve
4. score < 0.40 → send to admin for review
5. Admin approves/rejects via POST /api/admin/deals/{id}/approve|reject

Parser Failure Recovery:
───────────────────────
1. Parser fails (CSS selectors broke)
2. Raises ValueError
3. DiscoveryAgent reports via POST /api/deals/parser-error
4. EVENT: parser.failed published
5. ParserFixerAgent wakes up
6. Calls Claude to analyze HTML and suggest new selectors
7. Stores suggestion in config_settings table
8. DiscoveryLoop picks up new selectors on next run
9. Parsing succeeds ✓
```

---

## Prerequisites

```bash
# Python 3.10+
python --version

# Node.js 18+
node --version
npm --version

# PostgreSQL 12+
psql --version

# Environment variables
export DATABASE_URL="postgresql://user:pass@localhost/stocknotifier"
export ANTHROPIC_API_KEY="sk-ant-..."
export WEB_JWT_SECRET="your-secret-key-here"
```

---

## Setup Steps

### 1. Install Python Dependencies

```bash
pip install -U pip setuptools wheel
pip install -e .
```

### 2. Initialize Database

```bash
python scripts/init_db.py
```

This creates:
- `products` table (catalog)
- `stock` table (per-retailer availability)
- `prices` table (historical price tracking)
- `deals` table (curated good deals)
- `config_settings` table (editable config)
- `rules` table (user alert rules)

### 3. Build Frontend

```bash
cd frontend
npm install
npm run build
```

Outputs to `frontend/dist/` → served by FastAPI static routes.

### 4. Configure System

Edit `config.yaml`:

```yaml
stock:
  fetch:
    max_concurrent_requests: 4
    max_concurrent_playwright: 2
    http_client: curl_cffi
    curl_impersonate: chrome124

deals:
  scoring:
    threshold: 0.40  # Auto-approve above this
    repost_cooldown_hours: 24
    weights:
      lowest_90d: 0.35
      below_30d_median: 0.30
      discount_vs_mrp: 0.20
      cross_retailer_best: 0.15
      has_offers: 0.0
      aggregator_corroborated: 0.0

platform:
  sources:
    - type: amazon_deals
      seed_urls: ["https://amazon.in/deals"]
      poll_seconds: 3600
      minimum_discount_pct: 0.15
      max_links_per_seed: 50
    
    - type: flipkart_deals
      seed_urls: ["https://flipkart.com/offers/deals-today"]
      poll_seconds: 3600
      minimum_discount_pct: 0.15
      max_links_per_seed: 50
    
    - type: ajio_deals
      seed_urls: ["https://ajio.com/s/sale"]
      poll_seconds: 3600
      minimum_discount_pct: 0.15
      max_links_per_seed: 30
    
    - type: myntra_deals
      seed_urls: ["https://myntra.com/offers"]
      poll_seconds: 3600
      minimum_discount_pct: 0.15
      max_links_per_seed: 30
```

---

## Running the System

### Terminal 1: Backend API

```bash
uvicorn commerce_platform.web.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

Output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     Web API using DB postgresql://user:pass@localhost/stocknotifier
```

Frontend: http://localhost:8000 → serves React app from `dist/`

### Terminal 2: Worker Tasks

```bash
python -c "
import asyncio
from pathlib import Path
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers

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

Output:
```
INFO:     stock-runner started (will reload config every 15s)
INFO:     observation-processor started
INFO:     discovery-loop started (polling every 3600s)
INFO:     curation-loop started (reviewing every 300s)
INFO:     parser-fixer started (listening for failures)
```

---

## Testing the Complete Pipeline

### Test 1: Manual Discovery Report (Simulate Agent)

```bash
curl -X POST http://localhost:8000/api/deals/discover \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "amazon_deals",
    "seed_url": "https://amazon.in/deals",
    "items": [
      {
        "url": "https://amazon.in/dp/B09Y8JDNXL",
        "price_inr": 39999,
        "mrp_inr": 59990,
        "discount_pct": 0.33,
        "product_title": "PlayStation 5",
        "image_url": "https://...",
        "score": 0.75,
        "score_reasons": ["90-day low", "Below 30-day median"]
      }
    ],
    "items_qualified": 1,
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'

# Response
{
  "stored": 1,
  "created": 1,
  "updated": 0
}
```

### Test 2: View Pending Approval Deals

```bash
curl -X GET "http://localhost:8000/api/admin/deals/pending?minutes=60" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test 3: Admin Approves Deal

```bash
curl -X POST http://localhost:8000/api/admin/deals/1/approve \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "note": "Great deal on PS5"
  }'

# Response
{
  "ok": true,
  "deal_id": 1,
  "status": "approved"
}
```

### Test 4: Admin Rejects Deal

```bash
curl -X POST http://localhost:8000/api/admin/deals/2/reject \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Seller rating too low"
  }'

# Response
{
  "ok": true,
  "deal_id": 2,
  "status": "rejected",
  "reason": "Seller rating too low"
}
```

### Test 5: View Public Deals API

```bash
# Get all deals
curl "http://localhost:8000/api/deals?limit=10"

# Get deals by retailer
curl "http://localhost:8000/api/deals?retailer=amazon&min_discount=0.15&limit=10"

# Response
[
  {
    "id": 1,
    "product_url": "https://amazon.in/dp/B09Y8JDNXL?tag=console-21",
    "product_id": null,
    "retailer": "amazon",
    "price_inr": 39999,
    "mrp_inr": 59990,
    "discount_pct": 0.33,
    "score": 0.75,
    "score_reasons": ["90-day low"],
    "product_title": "PlayStation 5",
    "image_url": "...",
    "is_active": true,
    "first_seen_at": "2026-05-06T12:00:00Z",
    "last_confirmed_at": "2026-05-06T12:00:00Z"
  }
]
```

### Test 6: Public Frontend

Open browser:
```
http://localhost:8000/deals
```

Features:
- Auto-refresh every 90s
- Filter by retailer
- Filter by min discount
- Shows score bar, discount %, reasons
- "Buy" button with affiliate link

---

## Admin Interface

```
http://localhost:8000/admin
```

Tabs:
1. **Catalog & scraping** — Manage products, watches, scrapers
2. **Request Queue** — Review user requests to add products
3. **Web API** — JWT config, rate limits, registration settings

Note: Deals tab is available via API only (`/api/admin/deals/*`)

---

## Monitoring & Debugging

### Check Active Deals

```sql
SELECT id, retailer, product_title, price_paise/100 as price_inr, score, is_active
FROM deals WHERE is_active = true
ORDER BY score DESC, last_confirmed_at DESC
LIMIT 20;
```

### Check Parser Failures

```sql
SELECT key, value -> 'error', value -> 'timestamp'
FROM config_settings
WHERE key LIKE 'parser.error.%'
ORDER BY key DESC
LIMIT 5;
```

### Check Parser Suggestions

```sql
SELECT key, value -> 'suggested_selectors'
FROM config_settings
WHERE key LIKE 'parser.suggestion.%';
```

### Watch Live Logs

```bash
# Backend API
tail -f logs/api.log | grep -i "deals\|error"

# Workers
tail -f logs/workers.log | grep -i "discovery\|curation\|parser"
```

### Monitor Database

```sql
-- Deal stats
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active,
  SUM(CASE WHEN admin_status = 'approved' THEN 1 ELSE 0 END) as approved,
  SUM(CASE WHEN admin_status = 'rejected' THEN 1 ELSE 0 END) as rejected,
  AVG(score) as avg_score
FROM deals;

-- Per-retailer breakdown
SELECT 
  retailer,
  COUNT(*) as total,
  SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active,
  ROUND(AVG(score)::numeric, 3) as avg_score,
  ROUND(AVG(CAST(discount_pct AS numeric) * 100), 1) as avg_discount_pct
FROM deals
GROUP BY retailer
ORDER BY active DESC;
```

---

## Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Discovery per source | <1 hour | 60 min (configurable) |
| Parse per page (BS4+JSON-LD) | <1s | ~500ms |
| Score per item | <100ms | ~50ms |
| DB upsert per item | <50ms | ~20ms |
| Curation pass (review pending) | <5 min | ~30s |
| Admin approval response | <100ms | ~50ms |

---

## Deployment

### Docker Compose (Local)

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: stocknotifier
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    command: uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres/stocknotifier
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      WEB_JWT_SECRET: ${WEB_JWT_SECRET}
    depends_on:
      - postgres

  workers:
    build: .
    command: python worker_runner.py
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres/stocknotifier
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - postgres

volumes:
  postgres_data:
```

### Production Checklist

- [ ] Set `WEB_JWT_SECRET` to strong random value
- [ ] Set `ANTHROPIC_API_KEY` to actual key
- [ ] Disable `WEB_OPEN_REGISTRATION` in production
- [ ] Configure `CORS_ORIGINS` to specific domains
- [ ] Use PostgreSQL 12+ with SSL
- [ ] Run workers on separate VM/container
- [ ] Set up monitoring alerts (ParserFailed count > 5/hour)
- [ ] Backup database daily
- [ ] Use nginx/Caddy as reverse proxy
- [ ] Enable HTTPS only

---

## Troubleshooting

### API Won't Start

```bash
# Check port 8000 is free
lsof -i :8000

# Check DATABASE_URL
python -c "from commerce_platform.platform.config.loader import load; print(load('config.yaml').platform.store.dsn)"

# Check imports
python -c "from commerce_platform.web.main import create_app; print('OK')"
```

### Workers Won't Start

```bash
# Check asyncio compatibility
python -c "import asyncio; asyncio.run(asyncio.sleep(0))"

# Check config.yaml path
python -c "from pathlib import Path; print(Path('config.yaml').resolve())"

# Check database connection
PGPASSWORD=password psql -h localhost -U postgres -d stocknotifier -c "SELECT 1"
```

### Parser Keeps Failing

1. Check HTML in `config_settings[parser.error.{source_type}.html_snippet]`
2. Manually test selectors:
   ```python
   from bs4 import BeautifulSoup
   html = "..."
   soup = BeautifulSoup(html, "html.parser")
   items = soup.find_all(".DealCard-module__dealContent")  # Old selector
   # Try new selectors, find one that works
   ```
3. ParserFixerAgent will suggest new selectors within 5 min
4. Check `config_settings[parser.suggestion.{source_type}]`
5. On next poll cycle (within 60 min), new selectors are tested

### Deals Not Appearing

```bash
# Check discovery ran
SELECT * FROM config_settings WHERE key LIKE 'discovery.%' ORDER BY created_at DESC;

# Check deals were created
SELECT COUNT(*) FROM deals WHERE created_at > NOW() - INTERVAL '2 hours';

# Check curation happened
SELECT * FROM config_settings WHERE key LIKE 'curation.%' ORDER BY created_at DESC;

# Check admin approval (if threshold is high)
SELECT id, score, admin_status FROM deals ORDER BY created_at DESC LIMIT 10;
```

---

## Next Steps

### Immediate (This Week)
- [x] Backend infrastructure (discovery, curation, parser fixing)
- [x] Agent gateway API
- [x] Public DealsPage frontend
- [ ] Run end-to-end for 24 hours, monitor
- [ ] Adjust threshold/weights based on data

### Short-term (Next Week)
- [ ] Add FraudDetectionAgent (validate seller legitimacy)
- [ ] Add WebIntelligenceAgent (handle CAPTCHA, bot detection)
- [ ] Build Admin deals UI tab
- [ ] Set up Telegram/Discord notifications

### Medium-term (2 Weeks)
- [ ] Affiliate link rewriting per retailer
- [ ] Deal notifications (email, SMS, Telegram)
- [ ] Price history visualization
- [ ] Machine learning deal prediction

### Long-term (Monthly)
- [ ] Hermes Agent integration (persistent memory, skill evolution)
- [ ] Multi-tenant isolation (support third-party retailers)
- [ ] Agent marketplace (sell learned selector patterns)
- [ ] Cost optimization (batch processing, caching)

---

## Support

For issues:
1. Check logs: `tail -f logs/*.log`
2. Check database: `psql -d stocknotifier -c "SELECT * FROM deals LIMIT 5"`
3. Check config: `python -c "from commerce_platform.platform.config.loader import load; import json; print(json.dumps(load('config.yaml').dict(), indent=2))"`
4. Read code: Start with `commerce_platform/runtime/worker_bootstrap.py` to understand event flow

Good luck! 🚀
