# Architectural Issues - Deep Scan

## 1. **MONOLITHIC AGENT RESPONSIBILITIES** ⚠️ CRITICAL

### Problem
`DealDiscoveryAgent._process_item()` (lines 175-268) does 7+ distinct operations:
1. Retailer/ASIN detection
2. Catalog product lookup
3. PDP HTML fetching
4. HTML parsing
5. Deal scoring
6. Database upsert
7. Event publishing

### Impact
- Agent is 250+ lines
- Hard to test (requires full stack)
- Hard to reuse logic
- Changes in one area affect entire agent
- Can't parallelize independently

### Root Cause
Mixed concerns: business logic, data access, orchestration, event publishing all in one place.

**SOLUTION**: Extract into separate services:
- `RetailerDetector` - identify retailer from URL
- `CatalogService` - lookup products
- `PDPFetcher` - fetch and cache PDP HTML
- `DealAssembler` - combine listing + PDP data
- `DealPublisher` - handle upsert + events

---

## 2. **TIGHT COUPLING VIA LAZY IMPORTS** ⚠️ HIGH

### Problem
`DealDiscoveryAgent._process_item()` lines 177-178:
```python
from commerce_platform.stock.parsers.protocol import get_parser_for_source
from commerce_platform.web.listing_scrape import detect_retailer_and_asin
```

Imports inside function indicate circular dependencies or tight coupling.

### Impact
- Dependencies not visible at class level
- Can't mock for testing
- Harder to refactor dependencies
- Python imports are expensive (even if cached)

### Solution
Inject as constructor dependencies:
```python
def __init__(self, ..., parser_registry, retailer_detector):
    self._parser_registry = parser_registry
    self._retailer_detector = retailer_detector
```

---

## 3. **CONFIGURATION SCATTERED** ⚠️ HIGH

### Current State
- YAML: `platform.yaml` (sources, channels)
- Database: `config_settings` table (scoring threshold, admin channel)
- Code: Hardcoded values (5 minute window, 300s sleep)
- Constants: Some values extracted, some not

### Impact
- No single source of truth
- Hard to know what's configurable
- Risk of config mismatch between layers
- Testing with different configs is painful

### Solution
Single configuration layer:
```python
@dataclass
class PlatformConfig:
    sources: list[Source]
    scoring: ScoringConfig  # threshold, weights
    curation: CurationConfig  # approval_required, admin_channel
    discovery: DiscoveryConfig  # poll_interval, pending_approval_window
    logging: LoggingConfig
```

Loaded once at startup, injected everywhere. Database only for RUNTIME changes.

---

## 4. **EVENT BUS UNDER-UTILIZED** ⚠️ MEDIUM

### Problem
- Discovery agent publishes `PriceObservation` for catalog products (line 255)
- But directly upsertsDeals to table without event (line 227)
- Curator directly calls `mark_reviewed()` without event (line 65)

### Impact
- Non-discoverable flow (no way to know side effects)
- New features require modifying existing code
- Can't add observers (e.g., notify on deal approval without changing Curator)
- Tight coupling between agents

### Solution
Publish events for ALL state changes:
```python
# Instead of: await self._deal_repo.upsert(...)
# Do:
await self._bus.publish(DealCreated(deal=..., source=self.source_type))

# Curator auto-approval:
await self._bus.publish(DealApproved(deal_id=..., approved_by="curator", score=...))

# Admin approval:
await self._bus.publish(DealApproved(deal_id=..., approved_by="user:123", reason=...))
```

---

## 5. **REPOSITORY PATTERN VIOLATION** ⚠️ MEDIUM

### Problem
Repos are used, but:
- Discovery agent constructs `DealRow` directly and calls `upsert()` (line 227)
- This couples agent to data model
- Business logic mixed with data access

### Impact
- Can't change deal table schema without touching agent
- Agent knows too much about persistence details
- Violates Persistence Ignorance

### Solution
Repos should handle all state transitions:
```python
# Bad: Agent knows about DealRow
await deal_repo.upsert(DealRow(...))

# Good: Repo handles business logic
action = await deal_repo.create_or_update_deal(
    url=item.url,
    retailer=retailer,
    price_paise=int(price_inr * 100),
    score=deal_score.score,
    # ... other fields
)

# Repo internally:
# - Detects if this is new or update
# - Sets correct timestamp fields
# - Updates state machine (inserted → confirmed → price_improved)
# - Publishes events
```

---

## 6. **ERROR HANDLING - SILENT FAILURES** ⚠️ HIGH

### Problem
Pattern throughout codebase:
```python
try:
    await process()
except Exception:
    logger.exception("Failed")
    results["errors"].append(str(e))
    continue  # ← SILENT FAILURE
```

### Impact
- Agent keeps running even after failures
- Errors accumulate but don't propagate
- No retry logic
- No circuit breaker
- Could mask systemic issues

### Examples
- curator_agent.py:71-73 (curation failures silently continue)
- discovery_agent.py:208-209 (PDP parse failures silently skip)
- handler.py:36 (notification errors silently logged)

### Solution
Explicit error handling strategy:
```python
# TRANSIENT (retry) vs PERMANENT (skip) errors
try:
    result = await operation()
except TransientError:  # Network, timeout
    raise  # Let outer loop retry
except PermanentError:  # Invalid data, not found
    logger.warning("Skipping...")
    return None
except UnexpectedError:
    logger.exception("BUG")
    raise  # Crash and alert
```

---

## 7. **SEQUENTIAL DEPENDENCY HARDCODED AS PARALLEL** ⚠️ MEDIUM

### Problem
Worker bootstrap (line 217-244):
```python
tasks = [
    asyncio.create_task(StockRunner(...)),      # Fetches data
    asyncio.create_task(observation_processor()), # Evaluates rules
    asyncio.create_task(discovery_loop()),       # Finds deals
    asyncio.create_task(curation_loop()),        # Evaluates deals
    asyncio.create_task(parser_fixer_loop()),    # Auto-fixes parsers
]

await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
```

Flow should be: Discovery → Curation → Notification (sequential)
But they're launched as parallel tasks with fixed sleep intervals.

### Impact
- If discovery is slow, curation runs without pending deals
- If curation fails, no deals are sent (not async-safe)
- No backpressure mechanism
- Could accumulate pending deals if curation is slow

### Solution
Change to pipeline with channels:
```python
# discovery_queue → curation_queue → notification_queue
# Each stage can be scaled independently
deals_channel = asyncio.Queue()
approved_channel = asyncio.Queue()

tasks = [
    DiscoveryLoop(output=deals_channel),
    CurationLoop(input=deals_channel, output=approved_channel),
    NotificationLoop(input=approved_channel),
]
```

---

## 8. **SHARED MUTABLE STATE - RACE CONDITIONS** ⚠️ HIGH

### Problem
`RuleEngine._last_stock_state`:
```python
self._last_stock_state: dict[tuple[str, str], bool] = {}  # (product_id, retailer) → in_stock
```

Used to detect stock changes (line 114):
```python
prev_in_stock = self._last_stock_state.get(key, observation.in_stock)
if prev_in_stock != observation.in_stock:
    # Trigger rule
self._last_stock_state[key] = observation.in_stock
```

### Impact
- No thread safety (dict access)
- Two concurrent observations of same product could race
- Could miss state transitions
- Could trigger duplicate alerts

### Solution
Move state to database (single source of truth):
```python
# In StockRepo
async def get_last_known_state(product_id, retailer) -> bool | None:
    # Query DB with lock
    ...

async def record_observation(product_id, retailer, in_stock):
    # Atomic: detect change + update
    ...
```

---

## 9. **TESTABILITY - NO SEAMS FOR MOCKING** ⚠️ MEDIUM

### Problem
- All repos depend on actual `db.pool` (asyncpg connection)
- No interfaces/protocols for repos
- Can't test agents without real database
- Can't test in parallel (DB connections/locks)

### Impact
- Integration tests only (slow)
- Can't test error paths easily
- New developers can't test locally
- CI must have Postgres running

### Solution
Define protocols:
```python
class DealStore(Protocol):
    async def create_or_update(self, deal: DealInput) -> DealAction: ...
    async def get_pending_approval(self, minutes: int) -> list[Deal]: ...
    async def mark_reviewed(self, deal_id: int, status: ReviewStatus) -> None: ...

# Real implementation uses DB
class PostgresDealStore:
    def __init__(self, pool): ...

# Test implementation is in-memory
class InMemoryDealStore:
    def __init__(self):
        self.deals = {}
        ...
```

Then agents depend on `DealStore` protocol, not concrete class.

---

## 10. **DEAL SCORING POLICY HIDDEN IN SCORER** ⚠️ MEDIUM

### Problem
`DealScore` computes a numeric score, but business rules are hidden:
- Who approves what score?
- What does "catalog product" vs "unknown" mean?
- Why 5 minute window for curation review?
- Why auto-approve if score > threshold?

These are POLICIES that should be explicit, not implicit in code.

### Impact
- Admin can't control approval rules without code change
- No audit trail of why deal was approved
- Coupling between scorer and curator

### Solution
Explicit Deal Approval Policy:
```python
@dataclass
class DealApprovalPolicy:
    auto_approve_threshold: float = 0.75  # > this = auto-approve
    human_review_threshold: float = 0.40  # < this = send to human
    review_timeout_seconds: int = 1800
    catalog_product_priority: bool = True  # Catalog products score boost
    
class DealApprover:
    def __init__(self, policy: DealApprovalPolicy):
        self.policy = policy
    
    async def decide(self, deal: Deal) -> Decision:  # auto | manual | reject
        ...
```

---

## Summary of Architectural Debt

| Issue | Severity | Effort to Fix | Impact on Scale |
|-------|----------|---------------|-----------------|
| Monolithic agents | CRITICAL | 20 hours | Breaks at 10x load |
| Configuration scattered | HIGH | 8 hours | Hard to manage |
| Silent error handling | HIGH | 12 hours | Hides bugs in production |
| Shared mutable state | HIGH | 6 hours | Race conditions at concurrency |
| Event bus underused | MEDIUM | 10 hours | Hard to extend |
| Lazy imports | MEDIUM | 4 hours | Testing difficult |
| Repository pattern violation | MEDIUM | 8 hours | Schema changes risky |
| Sequential as parallel | MEDIUM | 6 hours | Throughput issues |
| No testability seams | MEDIUM | 14 hours | Slow tests |
| Hidden policies | LOW | 6 hours | Admin control limited |

**Total Debt**: ~94 hours of refactoring needed for production-grade system.

**Recommendation**: Start with #1 and #6 (biggest bang for buck: 20+12=32 hours to unlock testability + reliability).
