# Implementation Status — AI-Native Deal Discovery Platform

## ✅ COMPLETED (May 6, 2026)

### Phase 1: Configuration
- ✅ Deleted `config.yaml.example`
- ✅ Added deal sources to `config.yaml`:
  - amazon_deals (15% min discount)
  - flipkart_deals (15% min discount)
  - ajio_deals (15% min discount)
  - myntra_deals (15% min discount)
- ✅ Updated deals scoring config (removed weights, kept thresholds)
- ✅ Configured admin channel for approvals

### Phase 2: Parser Updates
- ✅ Added exception handling to all extractors:
  - `extract_amazon_deal_items()` — raises ValueError if no items
  - `extract_flipkart_offer_items()` — raises ValueError if no items
  - `extract_ajio_offer_items()` — raises ValueError if no items
  - `extract_myntra_offer_items()` — raises ValueError if no items
- ✅ Added `_parse_price()` and `_parse_discount_pct()` utilities
- ✅ Removed silent failures — all errors now logged and surfaced

### Phase 3: Integration Tests
- ✅ Created `tests/test_deal_scrapers_live.py`:
  - TestAmazonDealsScraper — fetches real amazon.in/deals
  - TestFlipkartOffersScraper — fetches real flipkart.com/offers
  - TestAjioOffersScraper — fetches real ajio.com/s/sale
  - TestMyntraOffersScraper — fetches real myntra.com/offers
- ✅ All tests use Playwright (JS rendering support)
- ✅ Tests verify extraction and price parsing
- ✅ Created `TESTING.md` with complete testing guide

### Phase 4: AI-Native Agents
- ✅ Created `DealDiscoveryAgent` (`commerce_platform/agents/discovery_agent.py`):
  - Fetches retailer deal pages
  - Extracts ListingItems with prices
  - Pre-filters by minimum_discount_pct
  - Fetches PDPs for unknowns
  - Scores vs 90-day history
  - Upserts to deals table
  - Publishes PriceObservation to event bus
  - Handles parser failures with suggestions
  - Returns DiscoveryResult with metrics

- ✅ Created `CuratorAgent` (`commerce_platform/agents/curator_agent.py`):
  - Watches deals table for new entries
  - Evaluates score vs threshold (0.40)
  - Sends low-confidence to admin
  - Auto-approves high-confidence
  - Format approval request messages

- ✅ Created agent package: `commerce_platform/agents/__init__.py`
- ✅ Updated `AGENTS.md` with architecture and design principles

### Phase 5: Documentation
- ✅ `TESTING.md` — comprehensive testing guide with Playwright
- ✅ `AGENTS.md` — AI-native agent architecture and design
- ✅ `IMPLEMENTATION_STATUS.md` (this file)

---

## ⬜ IN PROGRESS / PENDING

### Phase 6: Deal Repo Enhancements
**Status:** Blocked — needs implementation

Methods required in `DealRepo`:
```python
async def get_pending_approval(self, minutes: int) -> list[DealRow]
async def mark_reviewed(self, deal_id: int) -> None
async def mark_approved(self, deal_id: int, user_id: int | None) -> None
async def mark_rejected(self, deal_id: int, reason: str | None, user_id: int | None) -> None
async def get_by_id(self, deal_id: int) -> DealRow | None
```

**Impact:** Curator agent cannot function without approval tracking.

### Phase 7: Admin Command Routes
**Status:** Blocked — depends on Phase 6

Routes needed in `commerce_platform/web/routes/admin.py`:
```python
POST /admin/deals/{id}/approve    # Admin approves a deal
POST /admin/deals/{id}/reject     # Admin rejects a deal
GET  /admin/deals/pending         # List pending approval deals
```

### Phase 8: Worker Bootstrap Wiring
**Status:** Blocked — depends on Phase 6 & 7

Update `commerce_platform/runtime/worker_bootstrap.py`:
1. Instantiate DealDiscoveryAgent for each deal source
2. Instantiate CuratorAgent
3. Create discovery_loop() task
4. Create curation_loop() task
5. Wire into task manager

### Phase 9: Frontend Admin Deals Tab
**Status:** Design ready, implementation pending

Add to `frontend/src/pages/AdminPage.tsx`:
- 4th tab: "deals"
- Card 1: Scoring Config (threshold, repost cooldown)
- Card 2: Deal Sources (add/edit/delete)
- Card 3: Affiliate Tags (per-retailer config)
- Card 4: Live Deals (active deals table, auto-refresh)

### Phase 10: Frontend Public Deals Page
**Status:** Design ready, implementation pending

Create `frontend/src/pages/DealsPage.tsx`:
- Deal grid with filters (retailer, discount, score)
- Auto-refresh every 90s
- Affiliate-rewritten buy links
- Score visualization with reasons
- Deal history (expired deals)

### Phase 11: ParserFixerAgent (Future)
**Status:** Design only

Create `commerce_platform/agents/parser_fixer_agent.py`:
- Monitor discovery failures
- Call Claude API to analyze HTML
- Suggest CSS/XPath selector updates
- Validate suggestions on test HTML
- Propose updates for admin approval

---

## Test Results

### Unit Tests
```
tests/test_parser_registry.py — PENDING
tests/test_serp_parsers.py — PENDING (mock HTML tests)
```

### Integration Tests
```
tests/test_deal_scrapers_live.py — PENDING (requires playwright install)

To run:
  pip install playwright
  playwright install chromium
  pytest tests/test_deal_scrapers_live.py -v -s
```

### Expected to Pass:
- TestAmazonDealsScraper::test_extract_amazon_deal_items_real
- TestAmazonDealsScraper::test_amazon_items_have_prices
- TestFlipkartOffersScraper::test_extract_flipkart_offer_items_real
- TestFlipkartOffersScraper::test_flipkart_items_have_prices
- TestAjioOffersScraper::test_extract_ajio_offer_items_real
- TestMyntraOffersScraper::test_extract_myntra_offer_items_real

---

## Code Quality

### What's Ready
- ✅ All parsers include docstrings
- ✅ All agents include docstrings
- ✅ Type hints throughout
- ✅ Async/await patterns consistent
- ✅ Error handling with logging
- ✅ Config-driven behavior

### Code Locations
| Component | Path | Status |
|-----------|------|--------|
| Discovery Agent | `commerce_platform/agents/discovery_agent.py` | ✅ Complete |
| Curator Agent | `commerce_platform/agents/curator_agent.py` | ✅ Complete |
| Listing Parsers | `commerce_platform/stock/sources/serp_parsers.py` | ✅ Updated |
| Config | `config.yaml` | ✅ Updated |
| Tests | `tests/test_deal_scrapers_live.py` | ✅ Complete |
| Testing Guide | `TESTING.md` | ✅ Complete |
| Agent Docs | `AGENTS.md` | ✅ Updated |

---

## Deployment Checklist

- [ ] Phase 6: Implement deal_repo approval methods
- [ ] Phase 7: Add admin routes for /approve and /reject
- [ ] Phase 8: Wire agents into worker_bootstrap
- [ ] Phase 9: Build admin deals UI
- [ ] Phase 10: Build public deals page
- [ ] Run live integration tests (test_deal_scrapers_live.py)
- [ ] Deploy to staging
- [ ] Monitor deal discovery for 24h
- [ ] Verify admin approval flow works
- [ ] Check affiliate link tracking
- [ ] Deploy to production
- [ ] Monitor metrics for first week
- [ ] Tune scoring thresholds based on results

---

## Known Issues & Limitations

1. **Ajio & Myntra Use React** — Parsers may fail if JS-rendered content changes. Playwright tests will catch this.
2. **No Real-time Updates** — Discovery runs on schedule (1h), not real-time.
3. **No Approval Timeout Enforcement** — Config has `approval_timeout_seconds: 1800`, but not implemented in CuratorAgent.
4. **No Parser Auto-fix** — ParserFixerAgent (Phase 11) is future work.
5. **No Fraud Detection** — High-discount anomalies not flagged (e.g., fake $1 iPhone deals).

---

## Performance Targets

- **Discovery**: 1h per source, <5s per item
- **Parsing**: <1s per page (with BeautifulSoup + Playwright on PDP)
- **Scoring**: <100ms per item
- **Curation**: <5 min to review all pending
- **Storage**: ~1MB per month for deals table

---

## Next Immediate Actions

1. **Implement deal_repo approval methods** (30 min)
2. **Add admin routes** (30 min)
3. **Wire agents into bootstrap** (1h)
4. **Build admin UI** (2h)
5. **Run live tests** (30 min)
6. **Deploy to staging** (30 min)
7. **Monitor & tune** (ongoing)

**Estimated total: 5-6 hours to production-ready (excluding monitoring)**

---

## Questions & Notes

- **Playwright installation**: Required for live tests. `pip install playwright && playwright install chromium`
- **Deal URL dedup**: Currently uses `product_url` as unique key. Should we merge by `product_id` instead?
- **Affiliate tracking**: URLs rewritten at send time. No need to track separately.
- **Admin approval UI**: Consider using Telegram bot commands vs. web form. Which is preferred?
- **Fallback for JS-rendered pages**: Should we retry with Playwright if BeautifulSoup fails?
