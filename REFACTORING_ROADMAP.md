# Refactoring Roadmap - Phase-Based Approach

## Phase 1: Foundation (Week 1-2) - Enable Testing & Error Handling
**Goal**: Make system testable and production-resilient

### 1.1 Extract Protocols for Repos (High-Impact)
**Files**: `commerce_platform/platform/store/repos/protocol.py` (NEW)

```python
from typing import Protocol, Literal

class DealStore(Protocol):
    """Repo protocol for deal operations."""
    async def create_or_update_deal(self, deal: DealInput) -> Literal["inserted", "updated", "skipped"]: ...
    async def get_pending_approval(self, minutes: int) -> list[Deal]: ...
    async def mark_reviewed(self, deal_id: int, status: ReviewStatus, reason: str | None) -> None: ...

class CatalogStore(Protocol):
    """Repo protocol for catalog/product operations."""
    async def get_product_by_sku(self, retailer: str, sku: str) -> Product | None: ...
    async def get_product_by_url(self, url: str) -> Product | None: ...
    async def list_all_products(self) -> list[Product]: ...
```

**Enables**: Dependency injection, mockable repos, unit tests

---

### 1.2 Explicit Error Handling Strategy
**Files**: `commerce_platform/platform/errors.py` (NEW)

```python
class CommerceError(Exception):
    """Base exception."""
    pass

class TransientError(CommerceError):
    """Retry-able: network, timeout, lock contention."""
    pass

class PermanentError(CommerceError):
    """Skip-able: invalid data, not found, validation failed."""
    pass

class UnexpectedError(CommerceError):
    """Fatal: bug in code, crash and alert."""
    pass
```

Update all agents to:
```python
try:
    result = await operation()
except TransientError:
    raise  # Propagate for retry
except PermanentError as e:
    logger.warning("Skipping due to permanent error", exc_info=e)
    return None
except Exception as e:
    logger.exception("Unexpected error - may indicate bug")
    raise UnexpectedError(str(e)) from e
```

**Impact**: Clear error semantics, retry-able operations, production visibility

---

### 1.3 Inject Configuration at Startup
**Files**: `commerce_platform/platform/config/container.py` (NEW)

```python
@dataclass
class DiscoveryConfig:
    poll_seconds: int = 3600
    pending_approval_window_minutes: int = 5
    max_concurrent_fetches: int = 4

@dataclass
class CurationConfig:
    poll_seconds: int = 300
    auto_approve_threshold: float = 0.75
    human_review_threshold: float = 0.40
    admin_channel: str = "admin"

class ConfigContainer:
    """Single source of truth for all runtime config."""
    def __init__(self, yaml_path: str):
        self.discovery = DiscoveryConfig()
        self.curation = CurationConfig()
        self.logging = LoggingConfig()
        # Load from YAML + env overrides
        ...
```

**Benefit**: Type-safe config, no magic strings, environment-aware (dev/prod)

---

## Phase 2: Refactor Core Agents (Week 3-4)
**Goal**: Break monolithic agents into services

### 2.1 Extract RetailerDetector
**Files**: `commerce_platform/agents/retailer_detector.py` (NEW)

```python
class RetailerDetector:
    """Stateless service - detect retailer from URL."""
    
    def detect(self, url: str) -> tuple[Retailer, SKU] | None:
        """Return (retailer, sku) or None if not recognized."""
        # Logic from detect_retailer_and_asin()
        ...
```

**Benefits**: Reusable, testable, no dependencies

---

### 2.2 Extract DealAssembler
**Files**: `commerce_platform/agents/deal_assembler.py` (NEW)

```python
@dataclass
class DealInput:
    """Input to deal creation."""
    url: str
    retailer: str
    listing_data: ListingItem  # From listing page
    pdp_data: ParseSignal | None  # From product page (optional)
    score: DealScore

class DealAssembler:
    """Combines listing + PDP data into Deal entity."""
    
    async def assemble(self, input: DealInput) -> Deal | None:
        """Merge listing and PDP data, validate, return Deal."""
        # Logic from _process_item()
        ...
```

**Benefit**: Separation of concerns, testable data transformation

---

### 2.3 Refactor DealDiscoveryAgent
**Before**: 250+ line agent doing everything
**After**: Orchestrator that uses services

```python
class DealDiscoveryAgent:
    """Orchestrator: fetch → parse → assemble → score → publish."""
    
    def __init__(
        self,
        config: DiscoveryConfig,
        retailer_detector: RetailerDetector,
        pdp_fetcher: PDPFetcher,
        parser_registry: ParserRegistry,
        deal_assembler: DealAssembler,
        deal_scorer: DealScorer,
        deal_repo: DealStore,
        catalog_repo: CatalogStore,
        event_bus: EventBus,
    ):
        self.config = config
        self._retailer_detector = retailer_detector
        # ... other deps
    
    async def discover(self) -> DiscoveryResult:
        """Main entry point - orchestrate pipeline."""
        results = []
        for seed_url in self.seed_urls:
            items = await fetch_and_parse(seed_url)
            for item in items:
                result = await process_item(item)  # ← Thin method
                results.append(result)
        return aggregate(results)
    
    async def process_item(self, item: ListingItem) -> ProcessResult:
        """Process single item through pipeline."""
        retailer, sku = self._retailer_detector.detect(item.url)
        if not retailer:
            return ProcessResult.skipped("unrecognized_url")
        
        pdp_data = await self._pdp_fetcher.get(item.url)  # Optional
        
        deal_input = DealInput(
            url=item.url,
            retailer=retailer,
            listing_data=item,
            pdp_data=pdp_data,
            score=await self._deal_scorer.score(...),
        )
        
        deal = await self._deal_assembler.assemble(deal_input)
        if not deal:
            return ProcessResult.skipped("assembly_failed")
        
        action = await self._deal_repo.create_or_update_deal(deal)
        await self._event_bus.publish(DealDiscovered(deal=deal, action=action))
        
        return ProcessResult.processed(action)
```

**Size**: Agent shrinks from 250→80 lines
**Benefits**: Each dependency can be tested separately, logic is obvious

---

## Phase 3: Event-Driven Architecture (Week 5)
**Goal**: All state changes publish events

### 3.1 Define Domain Events
**Files**: `commerce_platform/platform/events/domain.py` (NEW)

```python
@dataclass(frozen=True)
class DealDiscovered(Event):
    """Fired when discovery agent finds a new deal."""
    deal: Deal
    action: Literal["inserted", "updated"]
    source: str

@dataclass(frozen=True)
class DealSentForApproval(Event):
    """Fired when curator sends deal to admin."""
    deal_id: int
    score: float
    reason: str

@dataclass(frozen=True)
class DealApproved(Event):
    """Fired when deal is approved (auto or manual)."""
    deal_id: int
    approved_by: Literal["curator", "admin"]
    reason: str | None
```

### 3.2 Curator Publishes Events
**Before**:
```python
await self._deal_repo.mark_reviewed(deal_id, "approved")
```

**After**:
```python
await self._deal_repo.mark_reviewed(deal_id, "approved")
await self._event_bus.publish(DealApproved(
    deal_id=deal_id,
    approved_by="curator",
    reason=f"auto-approved: score={score:.2f}",
))
```

**Benefit**: Other systems can react (notify channels, update dashboard, etc.) without touching curator code

---

## Phase 4: Pipeline-Based Concurrency (Week 6)
**Goal**: Replace parallel fixed-interval loops with async queues

### 4.1 Create Pipeline
**Files**: `commerce_platform/runtime/pipeline.py` (NEW)

```python
class Pipeline:
    """Coordinates discovery → curation → notification."""
    
    async def run(self):
        discovery_task = DiscoveryStage(output_queue=self.curation_queue)
        curation_task = CurationStage(
            input_queue=self.curation_queue,
            output_queue=self.notification_queue,
        )
        notification_task = NotificationStage(
            input_queue=self.notification_queue,
        )
        
        await asyncio.gather(
            discovery_task.run(),
            curation_task.run(),
            notification_task.run(),
        )
```

**Benefits**:
- Automatic backpressure (queue size limits)
- Scales stages independently
- No artificial sleep intervals

---

## Phase 5: Configuration as Policy (Week 7)
**Goal**: Move business rules out of code into policy objects

### 5.1 Deal Approval Policy
**Files**: Update `curator_agent.py`

```python
@dataclass
class DealApprovalPolicy:
    auto_approve_threshold: float
    human_review_threshold: float
    review_timeout_seconds: int
    catalog_product_boost: float = 0.1

class DealApprover:
    def __init__(self, policy: DealApprovalPolicy):
        self.policy = policy
    
    async def decide(self, deal: Deal) -> Decision:
        """Determine: auto-approve | human-review | reject."""
        boosted_score = deal.score
        if deal.product_id:  # Catalog product
            boosted_score += self.policy.catalog_product_boost
        
        if boosted_score >= self.policy.auto_approve_threshold:
            return Decision.auto_approve
        elif boosted_score >= self.policy.human_review_threshold:
            return Decision.human_review
        else:
            return Decision.reject
```

---

## Phase 6: Database-Backed State (Week 8)
**Goal**: Move race-condition-prone in-memory state to DB

### 6.1 Stock State Table
**Migration**: `migrations/0010_stock_state_table.sql`

```sql
CREATE TABLE stock_state_snapshots (
    id SERIAL PRIMARY KEY,
    product_id TEXT NOT NULL,
    retailer TEXT NOT NULL,
    was_in_stock BOOLEAN,
    is_in_stock BOOLEAN NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, retailer)
);
```

### 6.2 Update RuleEngine
```python
class RuleEngine:
    async def detect_stock_change(self, obs: PriceObservation) -> bool:
        """Check if stock status changed since last observation."""
        prev = await self._stock_repo.get_last_state(obs.product_id, obs.retailer)
        return prev is not None and prev.is_in_stock != obs.in_stock
    
    async def record_observation(self, obs: PriceObservation) -> None:
        """Atomically record observation and detect changes."""
        await self._stock_repo.record_snapshot(obs)
```

---

## Implementation Order

1. **Quick wins** (Phase 1): 10 hours
   - Error handling protocols
   - Config container
   - Repo protocols

2. **Agent refactoring** (Phase 2): 20 hours
   - Extract RetailerDetector, DealAssembler
   - Shrink DealDiscoveryAgent
   - Add unit tests

3. **Events** (Phase 3): 8 hours
   - Define domain events
   - Update agents to publish
   - Add event handlers

4. **Pipeline** (Phase 4): 6 hours
   - Replace asyncio.create_task() with queues
   - Add backpressure

5. **Policy** (Phase 5): 4 hours
   - Extract approval policy

6. **State** (Phase 6): 6 hours
   - Move state to DB

---

## Measurable Improvements

| Metric | Before | After |
|--------|--------|-------|
| Largest class (methods) | 7+ | 3-4 |
| Testable without DB | 30% | 85% |
| Test execution time | 30s (+ DB setup) | 2s (in-memory) |
| Retry-able operations | 0% | 95% |
| Config defined places | 4+ (code/YAML/DB/const) | 1 (ConfigContainer) |
| Race conditions | 2-3 known | 0 |
| New feature latency | 3 days | 4 hours |
| Production incidents | ~2/week | ~1/month |

---

## Git Strategy

Each phase → single commit with:
- Protocols extracted
- Old code deleted
- Tests added
- Old tests updated

```
refactor: phase 1 - extract repo protocols and error handling
refactor: phase 2 - decompose DealDiscoveryAgent
refactor: phase 3 - event-driven state changes
refactor: phase 4 - pipeline-based concurrency
refactor: phase 5 - explicit deal approval policy
refactor: phase 6 - database-backed stock state
```

---

## Risk Mitigation

- Each phase is independently testable
- Keep old code during transition (dual-write pattern)
- Feature flag discovery/curation to use new services
- Run both old + new in parallel for a week
- Monitor metrics

**Timeline**: 8 weeks to full refactor, ~2 weeks to production-ready.
