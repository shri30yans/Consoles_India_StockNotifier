# Agent-Based Deal Discovery System — Architecture & Operations

## System Overview

**Smart Split Architecture:**
- **Tier 1 (Traditional)**: BeautifulSoup + JSON-LD parsers for routine scraping (Amazon, Flipkart, Ajio, Myntra)
- **Tier 2 (Agents)**: Hermes-based intelligent agents for complex tasks, failures, and adaptation

```
Traditional Path (Fast)          Agent Path (Smart)
─────────────────────           ─────────────────
Amazon/Flipkart deal pages  →    ParserFixerAgent
BS4 + JSON-LD fallback      →    (auto-heals broken parsers)
→ deals table
                                 WebIntelligenceAgent
                                 (handles CAPTCHA, bot detection)

                                 FraudDetectionAgent
                                 (validates deal legitimacy)

                                 AdaptiveDiscoveryAgent
                                 (learns new retailers)
```

---

## Core Components

### 1. **Agent Gateway** (`commerce_platform/deals/agent_gateway.py`)

REST API for agent communication. Agents are **independent processes** that call these endpoints:

```bash
# Agent reports: I found deals
POST /api/deals/discover
{
  "source_type": "amazon_deals",
  "seed_url": "https://amazon.in/deals",
  "items": [
    {
      "url": "https://amazon.in/dp/...",
      "price_inr": 39999,
      "mrp_inr": 59990,
      "discount_pct": 0.33,
      "product_title": "PS5",
      "image_url": "...",
      "score": 0.85,
      "score_reasons": ["90-day low", "Below 30-day median"]
    }
  ],
  "items_qualified": 5,
  "timestamp": "2026-05-06T..."
}

Response: { "stored": 1, "created": 1, "updated": 0 }
```

```bash
# Agent reports: parser failed, here's why
POST /api/deals/parser-error
{
  "source_type": "amazon_deals",
  "seed_url": "https://amazon.in/deals",
  "error_message": "Failed to extract any items",
  "html_snippet": "<html>...(first 10KB)...</html>",
  "attempted_selector": ".DealCard-module__dealContent",
  "timestamp": "2026-05-06T..."
}

Response: { "ack": true, "message": "ParserFixerAgent will analyze this failure" }
```

```bash
# Agent reports: suspicious deal
POST /api/deals/alert
{
  "product_url": "https://...",
  "reason": "price_below_cost",
  "confidence": 0.92,
  "evidence": {
    "current_price": 999,
    "cost_estimate": 3000,
    "seller_rating": 2.1
  }
}

Response: { "ack": true, "for_admin_review": true }
```

---

### 2. **ParserFixerAgent** (`commerce_platform/agents/parser_fixer_agent.py`)

**When**: Parser fails (CSS selectors broke)  
**What it does**:
1. Receives `EVENT: parser.failed`
2. Analyzes HTML with Claude vision API
3. Suggests new CSS selectors
4. Stores suggestion in `config_settings` table
5. System picks up on next run

**Example flow**:
```
Parser fails: .DealCard-module__dealContent not found

ParserFixerAgent calls Claude:
  "Old selectors were .DealCard-module__dealContent
   Here's 5KB of new HTML. Find product containers."

Claude responds:
  "New selector: .dealCardContainer"

Agent stores: config_settings[amazon_deals.selector.card] = ".dealCardContainer"

Next poll: Discovery uses new selector, finds items ✓
```

**Key insight**: No human intervention needed. Agents continuously adapt.

---

### 3. **Discovery Loop** (in `worker_bootstrap.py`)

Runs traditional discovery in parallel:

```python
async def discovery_loop() -> None:
    """Poll each retailer, report via agent gateway."""
    for source in ["amazon_deals", "flipkart_deals", "ajio_deals", "myntra_deals"]:
        agent = DealDiscoveryAgent(source, ...)
        result = await agent.discover()
        
        if result.parser_suggestion:
            # Send to ParserFixerAgent via event
            await bus.publish(ParserFailed(...))
```

---

### 4. **Curation Loop** (in `worker_bootstrap.py`)

Auto-approves high-confidence deals, routes low-confidence to admin:

```
Deal score: 0.85 (above threshold 0.40)
  → Auto-approve (no admin needed)

Deal score: 0.35 (below threshold)
  → Send to admin for manual review
  → Admin: /approve or /reject
```

---

## Event Flow

```
┌─────────────────────────────────────────────────────────┐
│ Traditional Discovery (every 60 min)                    │
│ Amazon/Flipkart/Ajio/Myntra deal pages                 │
│ BS4 + JSON-LD fallback                                 │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ├─→ Success? POST /api/deals/discover
                   │                    │
                   │                    ▼
                   │           ┌─────────────────┐
                   │           │ Deals table     │
                   │           │ (upsert by URL) │
                   │           └─────────────────┘
                   │                    │
                   │                    ├─→ EVENT: deal.created
                   │                    │           (triggers CuratorAgent)
                   │                    │
                   │                    └─→ EVENT: price_improved
                   │                        (triggers notifications)
                   │
                   └─→ Failure? POST /api/deals/parser-error
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │ EVENT: parser.failed │
                       │                      │
                       │ ParserFixerAgent     │
                       │ wakes up:            │
                       │  1. Analyzes HTML    │
                       │  2. Calls Claude     │
                       │  3. Stores fix       │
                       │  4. Logs suggestion  │
                       └──────────────────────┘
```

---

## Running the System

### Start Web API + Workers:

```bash
# Terminal 1: Web API (FastAPI)
uvicorn commerce_platform.web.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --env-file .env \
  --reload

# Terminal 2: Workers (discovery, curation, parser fixing)
python -c "
import asyncio
from pathlib import Path
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers

config = load('config.yaml')
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

---

## Testing Agent Communication

```bash
# Test 1: Agent reports successful discovery
curl -X POST http://localhost:8000/api/deals/discover \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "amazon_deals",
    "seed_url": "https://amazon.in/deals",
    "items": [
      {
        "url": "https://amazon.in/dp/B123ABC",
        "price_inr": 39999,
        "mrp_inr": 59990,
        "discount_pct": 0.33,
        "product_title": "Product",
        "image_url": "https://...",
        "score": 0.85,
        "score_reasons": ["90-day low"]
      }
    ],
    "items_qualified": 1,
    "timestamp": "2026-05-06T12:00:00Z"
  }'

# Test 2: Agent reports parser failure
curl -X POST http://localhost:8000/api/deals/parser-error \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "amazon_deals",
    "seed_url": "https://amazon.in/deals",
    "error_message": "Failed to extract any items",
    "html_snippet": "<html>...</html>",
    "attempted_selector": ".DealCard-module__dealContent"
  }'

# Test 3: Fraud alert
curl -X POST http://localhost:8000/api/deals/alert \
  -H "Content-Type: application/json" \
  -d '{
    "product_url": "https://suspicious.com/deal",
    "reason": "price_below_cost",
    "confidence": 0.95,
    "evidence": {
      "listed_price": 500,
      "estimated_cost": 5000
    }
  }'
```

---

## Key Design Decisions

### 1. **Agents Don't Have DB Access**
Instead, they call REST endpoints. Benefits:
- ✅ Agents can run anywhere (different process, machine, container)
- ✅ Rate limiting at API level
- ✅ Logging centralized
- ✅ Easy to test (mock HTTP)

### 2. **Events Trigger Intelligence**
When `POST /api/deals/parser-error` fires:
- System publishes `EVENT: parser.failed`
- ParserFixerAgent subscribes
- ParserFixerAgent wakes up only when needed (efficient)
- Claude analysis happens in background

### 3. **Failures Are Signals, Not Crashes**
```python
if parser_error:
    POST /api/deals/parser-error  # Report, don't crash
    # System learns from failure
    # ParserFixerAgent suggests fix
    # Next run succeeds
```

---

## Extending with New Agents

### Add FraudDetectionAgent:

```python
# commerce_platform/agents/fraud_agent.py
class FraudDetectionAgent:
    async def validate_deal(self, deal_url: str, price: int) -> bool:
        """Check if deal looks legitimate."""
        # Call external APIs (seller rating, price history, etc.)
        # If suspicious: POST /api/deals/alert
        # If legitimate: return True

# In worker_bootstrap.py
async def fraud_check_loop():
    fraud_agent = FraudDetectionAgent(...)
    while True:
        pending = await deal_repo.list_pending_fraud_check()
        for deal in pending:
            if not await fraud_agent.validate_deal(deal.url, deal.price):
                # Already reported via POST /api/deals/alert
                pass
        await asyncio.sleep(300)  # Every 5 min
```

### Add WebIntelligenceAgent:

```python
# Handles: CAPTCHA, bot detection, Cloudflare, JavaScript rendering
# Uses: Playwright + undetected-chromedriver (looks like human)

class WebIntelligenceAgent:
    async def fetch_with_intelligence(self, url: str) -> str:
        """Fetch URL, handle CAPTCHA/bot detection."""
        try:
            # Try normal fetch first (fast)
            html = await http_fetcher.get(url)
        except BotDetected:
            # Bot detected, use stealth browser
            html = await self._fetch_with_playwright_stealth(url)
        except CaptchaDetected:
            # CAPTCHA, can't solve, report and skip
            await gateway.report_error(...)
        
        return html
```

---

## Monitoring & Debugging

### Check parser failures:
```sql
SELECT * FROM config_settings 
WHERE key LIKE 'parser.error.%' 
ORDER BY value ->> 'timestamp' DESC
LIMIT 10;
```

### Check parser suggestions:
```sql
SELECT * FROM config_settings 
WHERE key LIKE 'parser.suggestion.%';
```

### Fraud alerts:
```sql
SELECT * FROM config_settings 
WHERE key LIKE 'fraud.alert.%'
ORDER BY key DESC
LIMIT 5;
```

### Monitor discovery loop:
```bash
tail -f logs/worker.log | grep -i "discovery\|parser"
```

---

## Next Steps

### Phase 1: Stabilize (This session)
- [x] Decouple discovery via agent gateway
- [x] Implement ParserFixerAgent
- [ ] Run end-to-end, verify discovery works
- [ ] Test parser failure → fix cycle

### Phase 2: Extend (Next session)
- [ ] Add FraudDetectionAgent (validates deals)
- [ ] Add WebIntelligenceAgent (handles bot detection)
- [ ] Add AdaptiveDiscoveryAgent (learns new retailers)
- [ ] Build agent dashboard (success rate, failure patterns)

### Phase 3: Scale (Future)
- [ ] Multi-tenant agent isolation
- [ ] Agent skill marketplace (share learned selectors)
- [ ] Cost tracking per agent
- [ ] Failure prediction (alert before breaking)

---

## Architecture Benefits

✅ **Flexibility**: Add/remove agents without restarting core  
✅ **Resilience**: Failure in one agent doesn't crash system  
✅ **Learning**: Agents improve over time (skill evolution)  
✅ **Scalability**: Agents can run distributed  
✅ **Debugging**: Each agent has clear input/output  
✅ **Cost Efficiency**: Only run expensive operations (Claude) when needed  

This is the foundation for an **AI Agent Company** — flexible, scalable, self-healing.
