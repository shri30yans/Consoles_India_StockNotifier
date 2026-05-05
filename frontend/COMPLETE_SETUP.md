# Complete End-to-End Deal Discovery Platform

## Quick Start

```bash
# Terminal 1: API
uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Workers
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

Visit: http://localhost:8000/deals

## System Flow

1. **Discovery Loop** (every 60 min)
   - Poll: Amazon.in/deals, Flipkart/offers, Ajio/sale, Myntra/offers
   - Extract: Product URL, price, discount, image
   - Pre-filter: by minimum_discount_pct (15%)
   - Score: vs 90-day price history + MRP discount
   - Store: In deals table (upsert by URL)

2. **Curation Loop** (every 5 min)
   - Query: deals created/updated in last 5 min
   - Evaluate: score vs threshold (0.40)
   - Auto-approve: score >= threshold
   - Send to admin: score < threshold for review

3. **Parser Fixing** (when needed)
   - Listen: for parser failures (CSS selectors broke)
   - Analyze: HTML with Claude API
   - Suggest: new CSS selectors
   - Test: on next poll cycle
   - Result: parser auto-heals without intervention

## Key Features

✅ **Smart Discovery**: BS4 + JSON-LD fallback (survives CSS changes)
✅ **Self-Healing**: ParserFixerAgent auto-fixes broken parsers
✅ **Admin Approval**: Routes deals to admin for review
✅ **Public API**: /api/deals with retailer & discount filters
✅ **Affiliate Links**: Rewrite URLs with tracking tags
✅ **Event-Driven**: Decoupled agents via REST API
✅ **Observable**: Full logging and error tracking

## Testing

```bash
# Simulate agent discovering deal
curl -X POST http://localhost:8000/api/deals/discover \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "amazon_deals",
    "seed_url": "https://amazon.in/deals",
    "items": [{
      "url": "https://amazon.in/dp/B09Y8JDNXL",
      "price_inr": 39999,
      "mrp_inr": 59990,
      "discount_pct": 0.33,
      "product_title": "PlayStation 5",
      "image_url": "https://...",
      "score": 0.75,
      "score_reasons": ["90-day low"]
    }],
    "items_qualified": 1,
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'

# View public deals API
curl http://localhost:8000/api/deals?retailer=amazon&min_discount=0.15

# Admin approves deal
curl -X POST http://localhost:8000/api/admin/deals/1/approve \
  -H "Authorization: Bearer TOKEN" \
  -d '{"note": "Great deal"}'
```

## Architecture

```
Frontend (React)
    ↓ HTTP
FastAPI (Port 8000)
    ↓ SQL
PostgreSQL (deals table, config_settings, etc.)
    ↑ Events
Workers (Background Tasks)
├─ StockRunner (discovers deals)
├─ DiscoveryLoop (polls retailers)
├─ CurationLoop (reviews deals)
├─ ParserFixerAgent (fixes broken parsers)
└─ RuleEngine (evaluates user rules)
```

## Production Ready

- ✅ Type hints throughout
- ✅ Async/await patterns
- ✅ Error handling and logging
- ✅ Database migrations
- ✅ API authentication
- ✅ Event-driven architecture
- ✅ Comprehensive documentation

See AGENT_SYSTEM.md for detailed architecture.
See COMPLETE_SETUP.md for full setup instructions.

