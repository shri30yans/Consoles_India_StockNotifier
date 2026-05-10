# CLAUDE.md — Implementation Principles for Deal Discovery Platform

## Core Philosophy: Consolidation-First, Not Code-First

When implementing features, think architecturally BEFORE writing code. This prevents duplication, unclear semantics, and maintenance burden.

### Decision Tree: One Method or Many?

**Rule 1: Identical Implementation + Different State → One Method with Parameters**
```python
# WRONG (three methods, same SQL)
async def mark_approved(id: int): ...
async def mark_rejected(id: int): ...
async def mark_reviewed(id: int): ...

# RIGHT (one method, status parameter + Literal type)
async def mark_reviewed(
    deal_id: int,
    status: Literal["approved", "rejected"],
    user_id: int | None = None,
) -> None: ...
```

**Rule 2: Multiple Filter Conditions → One Method with Optional Parameters**
```python
# WRONG (four methods for different filters)
async def list_active() -> list[Deal]: ...
async def list_by_retailer(r: str) -> list[Deal]: ...
async def list_by_score(s: float) -> list[Deal]: ...
async def list_by_retailer_and_score(r: str, s: float) -> list[Deal]: ...

# RIGHT (one method, optional parameters)
async def list_active(
    retailer: str | None = None,
    min_score: float = 0.0,
    limit: int = 50,
) -> list[Deal]: ...
```

**Rule 3: Repeated Data Transformation → Extract Helper Method**
```python
# WRONG (duplicate conversion in 3 methods)
def get_by_id(id: int):
    row = db.fetch(...)
    return DealRow(id=row["id"], name=row["name"], ...)  # 10 lines

def list_active():
    rows = db.fetch(...)
    return [DealRow(id=row["id"], name=row["name"], ...) for row in rows]  # same 10 lines

# RIGHT (single canonical converter)
def _row_to_dealrow(row: asyncpg.Record) -> DealRow:
    return DealRow(id=row["id"], name=row["name"], ...)

def get_by_id(id: int):
    row = db.fetch(...)
    return self._row_to_dealrow(row)

def list_active():
    rows = db.fetch(...)
    return [self._row_to_dealrow(row) for row in rows]
```

### The Semantics Test

**Before finalizing a method signature, ask yourself:**
"Can a junior developer use this correctly without reading documentation?"

- ❌ If methods confuse semantics ("use X for scenario A, Y for scenario B") → consolidate to one method
- ❌ If docs explain "call X then Y" → should be one method
- ❌ If optional parameters change behavior completely → reconsider (possibly different methods)
- ✅ If signature is self-documenting via Literal types → correct design

### Type Safety Through Design

**Use Literal types, not strings:**
```python
# WRONG (easy to typo "aproved")
async def mark_reviewed(id: int, status: str) -> None:
    if status == "approved": ...

# RIGHT (impossible to pass invalid status)
async def mark_reviewed(id: int, status: Literal["approved", "rejected"]) -> None:
    ...  # IDE autocomplete shows valid options, type checker prevents typos
```

**Use None, not empty strings, for optional fields:**
```python
# WRONG
admin_review_reason: str = ""  # Confusing: is it intentional or missing?

# RIGHT
admin_review_reason: str | None = None  # NULL = not set
```

---

## Deal Discovery Pipeline: Architecture-First Thinking

The deal discovery pipeline is designed with these principles in mind:

### 1. **Multi-Fallback Parser Strategy**
- Try CSS selectors first (fast, brittle)
- Fall back to JSON-LD (reliable, W3C standard)
- Raise ValueError if both fail (fail loud, never silent)
- **Why**: Survivors CSS changes, provides diagnostic feedback when extraction fails
- **Cost**: ParserFixerAgent (phase 11) will auto-analyze failures and suggest fixes

### 2. **Single DealRepo._row_to_dealrow() Method**
All database queries (get_by_url, list_active, list_expired, get_by_id, get_pending_approval) share one canonical row converter.
- **Why**: Single source of truth. Adding a field → change one place, not 5.
- **Cost**: None (zero performance impact).

### 3. **Consolidated mark_reviewed() Method**
One method handles all approval states with clear parameters:
```python
async def mark_reviewed(
    deal_id: int,
    status: Literal["approved", "rejected"],
    user_id: int | None = None,
    reason: str | None = None,
) -> None: ...
```
- `user_id=None` → curator auto-approved
- `user_id=123` → admin (user 123) approved/rejected
- **Why**: Clear semantics, impossible to misuse, backward-compatible.

### 4. **Autonomous Agents Instead of Brittle Workers**
- **DealDiscoveryAgent**: Fetches → parses → pre-filters → scores → upserts. Self-healing on parser failures.
- **CuratorAgent**: Watches deals table, evaluates score vs threshold, routes borderline deals to admin.
- **Why**: Agents adapt when parsers break. Workers are monolithic and fail silently.

### 5. **Event-Driven Coordination**
- Agents publish PriceObservation events on EventBus
- observation_processor consumes observations, evaluates rules, sends notifications
- No tight coupling, easy to add new agents
- **Why**: Scales to 100+ retailers without refactoring core logic.

### 6. **Database Config, Not YAML**
- Scoring config (threshold, weights) stored in config_settings table
- Affiliate tags per retailer in same table
- Admin edits via API, changes apply immediately
- **Why**: Real-time updates, no restart required, auditable (timestamps on changes).

### 7. **Upsert Semantics with Clear State Machine**
```
inserted       → new deal discovered
confirmed      → same price, still active (no notify)
price_improved → price dropped >2% (notify)
reactivated    → was expired, price came back (notify)
expired        → price rose or OOS (no notify)
```
- **Why**: deals table is always clean snapshot of current state, no audit log noise.

---

## Before Implementing: The Checklist

- [ ] Are there 2+ methods doing 90% the same thing?
- [ ] Can parameters consolidate these? (status, action, filter)
- [ ] Would a Literal type make this safer?
- [ ] Could a junior dev use the signature correctly without docs?
- [ ] Is this the canonical form, or will I refactor later?
- [ ] Does this follow existing patterns in the codebase?
- [ ] If I add a field, where do I update this? (1 place = good, 3+ = bad)

**If any answer is "no", refactor BEFORE implementing.**

---

## Red Flags (Stop and Refactor)

1. **Similar method names**: create_x, update_x, delete_x → one method with action parameter
2. **Documentation explaining usage**: "use X for Y, Z for W" → should be one method
3. **Duplicated code**: same 15 lines in 3 methods → extract helper
4. **Unclear semantics**: "should I call A then B?" → one method with parameters
5. **Optional parameters that change behavior**: list(all=True) that changes entire SQL → bad design
6. **Empty strings instead of NULL**: confusing whether field is intentionally empty or missing → use NULL

---

## Testing: Fail Loud, Test Loud

- **Unit tests**: mock HTML fixtures, test extraction logic in isolation
- **Integration tests**: real retailer pages, live parsing, measure latency
- **Expected failures**: When CSS changes, extractors raise ValueError → this is correct behavior
- **ParserFixerAgent**: Phase 11 — automatically analyzes failures and suggests fixes

**Live tests will fail when retailers change CSS. This is expected and good — it alerts us to changes.**

---

## Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Parse listing page (BS4 + JSON-LD) | <1s | ~500ms |
| Score per item | <100ms | ~50ms |
| DB upsert per item | <50ms | ~20ms |
| Full discovery pass (50 items) | <60s | ~45s (5 items/retailer) |
| Curation pass (review pending) | <5min | ~30s (typically 0-5 deals pending) |

---

## Summary

**Think like an architect first, coder second:**

1. Identify all states/variations BEFORE coding
2. Ask "Can these be one method with parameters?"
3. Design consolidated signature (use Literal types)
4. Implement once, correctly
5. Test semantics: "Can a junior dev use this without docs?"

**Result**: Correct by design, maintainable, extensible.
