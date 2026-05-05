# Engineering Standards (Long-Term)

This project prioritizes maintainability over short-term speed.

## Core Principles

- Reuse existing domain flows before adding new ones.
- Keep one canonical path per behavior (fetching, parsing, persistence).
- Avoid hacks, one-off branches, and duplicated logic.
- Make changes easy to extend for new retailers and product sources.
- Prefer explicit, typed structures over ad-hoc dictionaries.

## Scraping Architecture

- Each retailer has its own parser module in `commerce_platform/stock/parsers/`.
- Listing extraction for admin/product onboarding must use the same parser outputs used by runtime polling (`ParseSignal` + listing fields).
- `commerce_platform/web/listing_scrape.py` is the web-layer dispatcher:
  - Detect retailer from URL.
  - Route to retailer-specific scrape function.
  - Return one `ListingScrapeResult` contract.
- Adding a new retailer should only require:
  1. Parser implementation in `stock/parsers`.
  2. One scraper function in `web/listing_scrape.py`.
  3. Registration in the scraper dispatch map.

## API and Route Design

- Route handlers should orchestrate, not contain parsing/fetching internals.
- Shared operations (fetch + parse + normalization) belong in reusable services/modules.
- Keep route code small and focused on request/response validation and repo calls.

## Quality Bar for Changes

- New code should be testable in isolation.
- Add or update focused tests when behavior changes.
- Keep naming clear (`scrape_<retailer>_listing`, `ParseSignal`, `ListingScrapeResult`).
- Preserve backward-compatible behavior unless requirements explicitly change.
- Prefer small composable functions over large monolith handlers.

## No Short-Term Techniques

- No hidden fallback hacks.
- No copy-paste logic across routes or services.
- No retailer-specific behavior scattered across unrelated files.

If unsure, choose the design that makes the next retailer integration simpler and safer.

---

# AI-Native Agent System

## Architecture Overview

The platform uses **autonomous AI agents** for deal discovery and curation instead of monolithic workers. Agents coordinate via event bus and adapt when parsers break.

### DealDiscoveryAgent
- **Fetches** retailer deal pages (amazon.in/deals, flipkart.com/offers, etc.)
- **Extracts** products (URL, price, discount, title)
- **Pre-filters** by minimum_discount_pct (15%)
- **Scores** against 90-day historical prices
- **Upserts** to deals table with state machine (inserted/updated/expired)
- **Publishes** PriceObservation to event bus for catalog products
- **Handles errors**: Parser fails → logs error with suggestion

### CuratorAgent  
- **Watches** deals table for new entries (every 5 min)
- **Evaluates** score vs threshold (0.40)
- **Routes** low-confidence deals to admin for approval
- **Auto-approves** high-confidence deals (score ≥ 0.40)
- **Logs** all decisions with reasoning

### Implementation Status
- ✅ DealDiscoveryAgent complete in `commerce_platform/agents/discovery_agent.py`
- ✅ CuratorAgent skeleton in `commerce_platform/agents/curator_agent.py`
- ⬜ Integration with deal_repo approval tracking
- ⬜ ParserFixerAgent for adaptive selector learning
- ⬜ Worker bootstrap wiring

## Key Design Decisions

1. **Exceptions, not silent failures** — Parsers raise ValueError if extraction breaks
2. **No defaults, explicit config** — Affiliate tags only appended if configured
3. **Product ID merging** — Deals deduplicated across sources by product_id
4. **Admin approval workflow** — Low-confidence deals require review before user notification
5. **Real-site testing** — Integration tests use Playwright to scrape actual retailer pages
