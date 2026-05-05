# System Monitoring & Troubleshooting Guide

## Quick Health Check

**All-in-one status:**
```bash
curl http://localhost:8000/health/system | jq
```

Output example:
```json
{
  "overall_status": "healthy",
  "checks": {
    "database": { "status": "healthy", "message": "PostgreSQL connection OK" },
    "deals": { 
      "status": "healthy",
      "active_deals": 47,
      "pending_approval": 3,
      "expired_deals": 12,
      "by_retailer": { "amazon": 15, "flipkart": 18, "ajio": 10, "myntra": 4 }
    },
    "api": { "status": "healthy" }
  }
}
```

---

## Verify Deal Discovery is Working

### Check 1: Are deals being discovered?

```bash
# See recent deals
curl http://localhost:8000/health/deals/recent | jq

# Check count
curl http://localhost:8000/health/deals | jq '.active_deals'
# Should be > 0 if discovery ran
```

### Check 2: Check per-retailer status

```bash
curl http://localhost:8000/health/deals | jq '.by_retailer'

# Output should show:
{
  "amazon": 15,    # Amazon deals found
  "flipkart": 18,  # Flipkart deals found
  "ajio": 10,      # Ajio deals found
  "myntra": 4      # Myntra deals found
}
```

### Check 3: Verify discovery loop ran

```bash
# Check database directly
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT 
  retailer,
  COUNT(*) as count,
  MAX(last_confirmed_at) as last_seen,
  AVG(score) as avg_score
FROM deals
WHERE is_active = true
GROUP BY retailer
ORDER BY last_seen DESC;
SQL
```

Expected: Timestamps from last hour showing recent polling

### Check 4: See what deals were discovered

```bash
curl "http://localhost:8000/api/deals?limit=10" | jq '.[] | {title, retailer, price_inr, discount_pct, score}'
```

Output:
```json
[
  {
    "title": "PlayStation 5",
    "retailer": "amazon",
    "price_inr": 39999,
    "discount_pct": 33.3,
    "score": 0.75
  }
]
```

---

## Verify Product Status & Stock Tracking

### Check 1: Is stock tracking working?

```bash
psql -h localhost -U postgres -d stocknotifier << 'SQL'
-- Check recent price observations
SELECT product_id, retailer, price_paise/100 as price_inr, in_stock, captured_at
FROM prices
ORDER BY captured_at DESC
LIMIT 20;
SQL
```

### Check 2: Products with watch rules

```bash
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT name, COUNT(*) as watch_count FROM products 
LEFT JOIN rules ON products.id = rules.product_id
GROUP BY name
HAVING COUNT(*) > 0
ORDER BY watch_count DESC
LIMIT 10;
SQL
```

### Check 3: Check if notifications would be sent

```bash
psql -h localhost -U postgres -d stocknotifier << 'SQL'
-- Products that have price drops ready to notify
SELECT p.name, p.id, COUNT(*) as alert_count
FROM products p
JOIN rules r ON p.id = r.product_id
WHERE r.threshold_paise IS NOT NULL
GROUP BY p.id, p.name
LIMIT 10;
SQL
```

---

## Verify Deal Approval Workflow

### Check 1: Deals pending admin approval

```bash
curl "http://localhost:8000/health/deals/pending-approval" | jq
```

Shows deals that scored below threshold and need manual review

### Check 2: Admin approved deals

```bash
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT id, product_title, retailer, score, admin_status, admin_reviewed_at
FROM deals
WHERE admin_status IS NOT NULL
ORDER BY admin_reviewed_at DESC
LIMIT 20;
SQL
```

### Check 3: Manually approve a deal (for testing)

```bash
# Get a pending deal ID first
curl "http://localhost:8000/health/deals/pending-approval" | jq '.[0].id'

# Approve it (replace DEAL_ID and TOKEN)
curl -X POST "http://localhost:8000/api/admin/deals/DEAL_ID/approve" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note": "Approved from monitoring"}'
```

---

## Check Parser Health

### Issue: "Parser failed for amazon_deals"

**Diagnosis:**

```bash
# Check parser error logs
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT key, value->>'error', value->>'timestamp'
FROM config_settings
WHERE key LIKE 'parser.error.%'
ORDER BY value->>'timestamp' DESC
LIMIT 5;
SQL
```

**What it means:**
- CSS selectors broke (website structure changed)
- JSON-LD extraction failed
- Network issue

**Solution:**
```bash
# 1. ParserFixerAgent should be analyzing this
# 2. Check if it suggested new selectors
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT key, value->>'suggested_selectors'
FROM config_settings
WHERE key LIKE 'parser.suggestion.%';
SQL

# 3. If suggestion exists, next poll will test it
# 4. If no suggestion, check worker logs:
tail -f logs/workers.log | grep -i "parser\|claude"
```

### Issue: "Playwright timeout for Ajio"

**Diagnosis:**

```bash
# Check if it's a Playwright issue or network
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT value->>'error'
FROM config_settings
WHERE key = 'parser.error.ajio_deals'
LIMIT 1;
SQL
```

**Solutions:**
- Increase timeout in config.yaml: `playwright_timeout_seconds: 30` (default 10)
- Check if Ajio changed to bot detection
- Try manual test with Playwright

---

## Performance Monitoring

### Check 1: Discovery latency

```bash
# Time between polls
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT 
  retailer,
  MAX(last_confirmed_at) as last_updated,
  NOW() - MAX(last_confirmed_at) as time_since_update
FROM deals
WHERE is_active = true
GROUP BY retailer;
SQL
```

**Expected:** Last updated < 60 minutes ago (discovery runs hourly)

### Check 2: Score distribution

```bash
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT 
  COUNT(*) as count,
  ROUND(AVG(score), 2) as avg_score,
  MIN(score) as min_score,
  MAX(score) as max_score
FROM deals
WHERE is_active = true;
SQL
```

**Expected:** avg_score around 0.4-0.6

### Check 3: Approval ratio

```bash
psql -h localhost -U postgres -d stocknotifier << 'SQL'
SELECT 
  admin_status,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deals WHERE admin_status IS NOT NULL), 1) as percentage
FROM deals
WHERE admin_status IS NOT NULL
GROUP BY admin_status;
SQL
```

**Expected:** ~60% approved, ~40% rejected

---

## Real-Time Monitoring

### Live deal discovery (tail logs)

```bash
# Terminal 1: Watch worker logs
tail -f logs/workers.log | grep -i "discovery\|discovery-loop\|upsert"

# Should show:
# INFO: Discovery: amazon_deals — found=47 qualified=12 created=3 updated=2
# INFO: Discovery: flipkart_deals — found=38 qualified=8 created=2 updated=0
```

### Live curation (tail logs)

```bash
# Terminal 2: Watch curation logs
tail -f logs/workers.log | grep -i "curation\|auto-approved\|pending"

# Should show:
# INFO: Curation: pending=3 sent_to_admin=2 approved=1
```

### Live parser fixing (tail logs)

```bash
# Terminal 3: Watch parser fixing
tail -f logs/workers.log | grep -i "parser\|fixer"

# Should show:
# INFO: ParserFixerAgent analyzing failure for amazon_deals
# INFO: Claude suggested selectors: {".dealContainer": ".DealCard-module__dealContent"}
```

---

## Common Issues & Fixes

### Issue: "No deals discovered"

**Checklist:**
- [ ] Discovery loop is running: `tail -f logs/workers.log | grep discovery-loop`
- [ ] Network is working: `curl https://amazon.in/deals` (should return HTML)
- [ ] Parsers are finding items: `curl http://localhost:8000/health/system | jq '.checks.deals'`
- [ ] Deals table has rows: `psql -c "SELECT COUNT(*) FROM deals"`

**Fix:**
```bash
# Manually trigger discovery for one retailer
python << 'PYEOF'
import asyncio
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from commerce_platform.stock.deal_discovery_watcher import DealDiscoveryWatcher
from pathlib import Path

async def test():
    config = load(Path('config.yaml'))
    db = Database(config.platform.store)
    await db.open()
    # This will show exact error
    source = config.platform.sources[0]  # amazon_deals
    # Create watcher and run
    print(f"Testing {source.type}...")

asyncio.run(test())
PYEOF
```

### Issue: "Parser keeps failing"

**Diagnosis:**
```bash
# See what error is being reported
curl "http://localhost:8000/health/deals/recent" | jq '.[0]'

# Check HTML snippet that failed
psql -c "SELECT value->>'html_length' FROM config_settings WHERE key LIKE 'parser.error.amazon_deals' LIMIT 1"
```

**Solution:**
1. ParserFixerAgent will auto-fix within 5 minutes
2. Check suggestion: `curl "http://localhost:8000/health/system" | jq '.checks.deals'`
3. If no suggestion, manually test selectors
4. Next poll cycle should succeed

### Issue: "Deals stuck at threshold"

**Problem:** Deals below 0.40 score not being approved

**Diagnosis:**
```bash
# Check threshold config
psql -c "SELECT * FROM config_settings WHERE key LIKE 'deals.%'"

# Check deal scores
psql -c "SELECT score, COUNT(*) FROM deals GROUP BY ROUND(score, 1) ORDER BY score"
```

**Solution:**
1. Lower threshold if too strict
2. Check if scores are being calculated correctly
3. Manually review and approve deals via API

---

## Monitoring Dashboard (Recommended)

Create `monitor.py` to watch live:

```python
import asyncio
import time
from datetime import datetime
from commerce_platform.platform.config.loader import load
from commerce_platform.platform.store.db import Database
from pathlib import Path

async def monitor():
    config = load(Path('config.yaml'))
    db = Database(config.platform.store)
    await db.open()
    
    while True:
        active = await db.deal_repo.list_active(limit=10000)
        pending = await db.deal_repo.get_pending_approval(minutes=5)
        
        # Count by retailer
        by_retailer = {}
        for deal in active:
            by_retailer[deal.retailer] = by_retailer.get(deal.retailer, 0) + 1
        
        # Clear screen and print
        print("\033[2J\033[H")  # Clear screen
        print(f"=== Deal Discovery Monitor === {datetime.now().strftime('%H:%M:%S')}")
        print(f"\nActive Deals: {len(active)}")
        print(f"Pending Approval: {len(pending)}")
        print(f"\nBy Retailer:")
        for r, c in by_retailer.items():
            print(f"  {r}: {c}")
        
        await asyncio.sleep(5)

asyncio.run(monitor())
```

Run:
```bash
python monitor.py
```

---

## Summary: How to Verify Everything Works

| Component | Check Command | Expected Result |
|-----------|--|--|
| **API** | `curl http://localhost:8000/health` | `{"status":"ok"}` |
| **Database** | `curl http://localhost:8000/health/system` | `overall_status: healthy` |
| **Deals Discovered** | `curl http://localhost:8000/api/deals` | Array with deals |
| **Discovery Loop** | `tail -f logs/workers.log \| grep discovery` | "found=X qualified=Y created=Z" |
| **Curation Loop** | `tail -f logs/workers.log \| grep curation` | "sent_to_admin=X approved=Y" |
| **Parser Health** | `curl http://localhost:8000/health/deals/recent` | Recent deals list |
| **Pending Approval** | `curl http://localhost:8000/health/deals/pending-approval` | List of deals < 0.40 score |
| **Frontend** | Open http://localhost:8000/deals | Deal grid with 5+ deals |

Once all checks pass, you have a fully operational deal discovery platform! ✓
