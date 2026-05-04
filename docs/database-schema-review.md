# Database schema review — tables, query patterns, and optimizations

This document describes the **PostgreSQL schema as exercised by application code** (`commerce_platform/platform/store/repos/*.py`, web routes, workers). It leads with **§1 — use cases and when each query runs**, then table inventory, consolidation ideas, and checklists.

**Indexes:** Runnable statements for current hot paths live in [`scripts/sql/recommended_indexes.sql`](../scripts/sql/recommended_indexes.sql) (identifiers, `price_snapshots`, `catalog_product_alerts`, `catalog_watches`, `catalog_rules`, `tracking_requests`, `app_users`). See **§7** for DBA caveats on that script.

> **Important:** `scripts/init_db.py` is **out of date** relative to the running app (different `price_snapshots`, `stock_state`, and `tracking_requests` shapes). Treat the repos as source of truth until `init_db` is reconciled or replaced by migrations.

---

## 1. Use cases → when the DB runs → how to keep it fast

Think in **moments** (who, what just happened), then **queries**, then **indexes / batching / caching**. Below is ordered roughly by **read traffic** first, then **write-heavy workers**.

### 1.1 Visitor opens the product list (`GET /api/products`)

| | |
|--|--|
| **When** | Every catalog page load; sort changes refetch. |
| **Goal** | Names + aggregate stock + “last signal” time — small JSON response. |
| **Queries** | ① `load_merged_platform_config` → `list_overlay_as_products`: `SELECT` all `catalog_products`, all `catalog_watches`, all `catalog_product_alerts` (three round-trips today). ② Build all `(product_id, retailer)` pairs from merged watches. ③ **`get_latest_snapshots_batch`** + **`get_batch`** on `price_snapshots` / `stock_state` (two queries — good). |
| **Hot?** | Yes — user-facing, bursty. |
| **Make fast** | Indexes on `(product_id, retailer, captured_at DESC)` and batch paths (already done for snapshots/stock). Optional: **run the three catalog SELECTs in parallel** inside `list_overlay_as_products`, or cache merged config for a few seconds if YAML+DB rarely change. At large scale: **denormalize** “list row” fields on `catalog_products` to skip snapshot joins for the index API only. |

---

### 1.2 Visitor opens one product (`GET /api/products/{id}`, then `/status`)

| | |
|--|--|
| **When** | After navigation (detail first, then status in the SPA). |
| **Goal** | Static-ish metadata + per-retailer stock/price/last check. |
| **Queries** | **Each** of detail and status calls **`load_merged_platform_config`** again (stateless HTTP — **full** overlay: three catalog SELECTs + YAML read **per request**, twice if both endpoints fire). Then status: **batch** snapshots + stock for that product’s watches (good). Price chart: `list_price_series` — range scan on `price_snapshots`. |
| **Hot?** | Medium per user; **worse than it looks** because merge is duplicated across detail/status/chart. |
| **Make fast** | Same `price_snapshots` index as §1.1; **cache or share merged config** within a short window, or add **DB/API “product by id”** without reloading every product’s watches/alerts. |

---

### 1.3 Visitor opens price history (`GET /api/products/{id}/price-series`)

| | |
|--|--|
| **When** | Chart / history UI. |
| **Queries** | `WHERE product_id = ? [AND retailer = ?] AND captured_at >= ? ORDER BY captured_at` (bounded `LIMIT`). |
| **Hot?** | Low–medium. |
| **Make fast** | Composite index **`(product_id, retailer, captured_at)`**; retention/partitioning if the table grows. |

---

### 1.4 User registers / logs in (`/api/auth/*`)

| | |
|--|--|
| **When** | Registration, login, token refresh paths that hit DB. |
| **Queries** | `app_users` by **`email`** (lookup / uniqueness); **`id`** after insert. |
| **Hot?** | Medium spikes at sign-up. |
| **Make fast** | **Btree on `email`** (see `recommended_indexes.sql`). Emails are normalized to lower case on insert — index matches `WHERE email = $1`. |

---

### 1.5 User submits “track this” (`tracking` routes)

| | |
|--|--|
| **When** | Create request; list “my requests”. |
| **Queries** | `INSERT tracking_requests`; `SELECT … WHERE user_id = ? ORDER BY created_at DESC`. |
| **Hot?** | Low per user. |
| **Make fast** | **`(user_id, created_at DESC)`** index. |

---

### 1.6 Admin reviews queue / approves (`admin` + `tracking_repo`)

| | |
|--|--|
| **When** | Admin opens pending list; open one request; approve/reject. |
| **Queries** | `list_by_status` / `list` all; `get(id)`; `UPDATE tracking_requests`; **`catalog_repo.ensure_product_and_add_watch`** (writes products, watches, identifiers, rules as applicable). |
| **Hot?** | Low frequency, **high write complexity** per approval. |
| **Make fast** | **`(status, created_at DESC)`** for queue; keep approval logic in a **transaction**. Some admin paths **`list_product_ids` then `list_watches_for_product` per id** — if that page is slow, batch “all watches” in one query `WHERE product_id = ANY($1::text[])`. |

---

### 1.7 Workers — every stock poll (continuous, high write volume)

| | |
|--|--|
| **When** | Each `(product, watch)` interval fires; after each successful parse. |
| **Queries** | **`stock_state` upsert** (always); **`price_snapshots` insert** when price/MRP present. |
| **Hot?** | **Highest sustained write rate** in the system. |
| **Make fast** | **`UNIQUE(product_id, retailer)`** (or PK on those columns) backs **`ON CONFLICT … DO UPDATE`** — good. Today `stock_repo.upsert` still runs a **read** (`SELECT in_stock, last_changed_at`) inside the same transaction before write — two round-trips to the same row per poll; a DBA-tuned path could use **`INSERT … ON CONFLICT DO UPDATE`** with **`EXCLUDED`** / `stock_state.in_stock` in one statement to drop the pre-read where semantics allow. For snapshots: focus on **index**, **autovacuum**, and **retention** (inserts are single-row; batch insert only helps if you pipeline in app code). |

---

### 1.8 Workers — wishlist parse (every N seconds per list)

| | |
|--|--|
| **When** | Each item row after HTML parse. |
| **Queries** | **`get_product_id_by_retailer_sku(retailer, sku)`** — **one round-trip per item** today. |
| **Hot?** | Medium — can be 10–50 queries per cycle. |
| **Make fast** | **`(retailer, sku)`** index on `catalog_product_identifiers`. Better: **batch resolve** — `SELECT product_id, retailer, sku FROM … WHERE (retailer, sku) IN ((‘amazon’, ‘B0…’), …)` in one query per page. |

---

### 1.9 Workers — rule reload (`RuleEngine.reload_rules`)

| | |
|--|--|
| **When** | Worker startup + every `config_reload_seconds`. |
| **Queries** | Full scan **`catalog_rules WHERE enabled`** (plus JSON parse of channels). |
| **Hot?** | Periodic; dataset usually small. |
| **Make fast** | Partial index **`(product_id) WHERE enabled`** if rule count grows; avoid loading disabled rows. |

---

### 1.10 Internal — observability / SSE (`build_status_payload`)

| | |
|--|--|
| **When** | Dashboard subscribers; periodic refresh. |
| **Goal** | Same per-watch “latest snapshot + stock” as the public product list, plus YAML-derived URLs. |
| **Queries** | Today: **per watch** `get_latest_snapshot` + `get` → **2 × (#watches) round-trips** (N+1). |
| **Hot?** | Can be painful if many watches. |
| **Make fast** | **Reuse `get_latest_snapshots_batch` + `get_batch`** over the same pair list as `/api/products` — identical logical need, one code path. |

---

### 1.11 Cross-cutting: merged config load (`load_merged_platform_config`)

| | |
|--|--|
| **When** | Almost every API that needs products; worker loops; observability. |
| **Queries** | `list_overlay_as_products` → products, watches, alerts (sequential). |
| **Hot?** | Amplifies every request above. |
| **Make fast** | Short **TTL cache** of merged `ProductConfig[]` in-process; or parallelize the three SELECTs; eventual **product-by-id** endpoint to skip full overlay for single-product reads. |

---

### 1.12 Quick reference — use case → tables → primary lever

| Use case | Main tables | Primary “fast” lever |
|----------|-------------|----------------------|
| Catalog list | `catalog_*`, `price_snapshots`, `stock_state` | Batch snapshot/stock ✓; index snapshots; optional cache merge |
| Product status / chart | `price_snapshots`, `stock_state` | Same + series index |
| Auth | `app_users` | Index `email` |
| Tracking | `tracking_requests` | Index `user_id`, `status` |
| Admin queue | `tracking_requests`, `catalog_*` | Queue index; transactional writes |
| Stock / wishlist workers | `stock_state`, `price_snapshots`, identifiers | Index `(retailer,sku)`; **batch** identifier lookup; stock upsert on unique key |
| Rule reload | `catalog_rules` | Partial index `enabled`; small table |
| Observability | same as list + merge | **Batch** snapshot/stock (fix N+1) |

---

## 2. Table inventory

### 2.1 `catalog_products`

**Purpose:** Canonical product identity and display metadata for the tracker.

**Columns (from `CatalogRepo`):** `id` (PK), `name`, `brand`, `category`, `emoji`, `colour`, `source_request_id`, `created_at`, `image_url`.

| Needed? | Notes |
|--------|--------|
| **Yes** | Core entity; referenced by watches, snapshots, stock, identifiers, rules. |
| `emoji`, `colour` | Optional UX; safe to null. |
| `source_request_id` | Optional trace back to `tracking_requests`; useful for ops, not for polling. |
| `created_at` as **TEXT** (ISO) | Works but **prefer `timestamptz`** for sorting, ranges, and index-friendly ordering without string comparison quirks. |

**Indexes:** PK on `id` is enough for joins; listing all products is typically full scan by design (small cardinality).

---

### 2.2 `catalog_watches` (current) → **target: JSON on `catalog_products`**

**Purpose today:** Which URL/source to poll per product — one row per watch.

**Target design (fewer tables):** Drop `catalog_watches` and store per-retailer config + scrape freshness on the product row, e.g. **`listings JSONB`**:

```json
{
  "amazon": {
    "url": "https://…",
    "poll_seconds": 60,
    "last_scraped_at": "2026-05-04T12:00:00+00:00"
  },
  "flipkart": { "url": "…", "last_scraped_at": null }
}
```

At minimum you need **`retailer → last_scraped_at`** for “when did we last hit this store”; the poller still needs **`url`** (and optionally `poll_seconds`) per retailer — keep them in the same object so one row replaces the watch table. Workers then **read-merge-write** that JSON (or use `jsonb_set`) when a scrape finishes.

| Needed? | Notes |
|--------|--------|
| **Today** | Table still used by code — migration required to move to JSON. |
| **After migration** | Table removed; index `idx_catalog_watches_product_id` from `recommended_indexes.sql` no longer applies. |

---

### 2.3 `catalog_product_alerts`

**Purpose:** Per-product alert definitions merged into `ProductConfig.alerts` when building the overlay (`list_overlay_as_products`). JSON in `channels`; optional `retailers` JSON.

| Needed? | Notes |
|--------|--------|
| **Yes** if you use DB-stored alert rows | Distinct from `catalog_rules` (see below). |
| **Redundant risk** | If everything is moved to `catalog_rules` only, this table becomes **candidates for removal** after a migration path — today both exist with different consumers. |

**Indexes:** `(product_id, position)` for ordered reads.

---

### 2.4 `catalog_rules`

**Purpose:** Rows consumed by `RuleEngine.list_all_rules` — notification rules (stock / price / discount) with `channels`, optional `retailers`, thresholds, `enabled`, `position`.

| Needed? | Notes |
|--------|--------|
| **Yes** for server-side alerting | Not the same row shape as `catalog_product_alerts`; admin/API may write here. |

**Indexes:** `(product_id)`, partial index `WHERE enabled = true` if rule count grows.

---

### 2.5 `catalog_product_identifiers` — **keep as a normal table (not JSON)**

**Purpose:** Map external SKUs (e.g. Amazon ASIN) → `product_id` for wishlist and “resolve this link / ASIN” flows.

**Columns:** `product_id`, `retailer`, `sku`, `created_at`; **UNIQUE(`product_id`, `retailer`)**.

| Needed? | Notes |
|--------|--------|
| **Yes — keep separate** | Collapsing identifiers into JSON on `catalog_products` makes **`WHERE retailer = $1 AND sku = $2`** expensive unless you add GIN / expression indexes and still fight JSON ergonomics. A **narrow lookup table** matches how wishlist ingestion resolves arbitrary URLs to a product. |

**Indexes:** **`(retailer, sku)`** btree — see [`scripts/sql/recommended_indexes.sql`](../scripts/sql/recommended_indexes.sql). The existing UNIQUE(`product_id`, `retailer`) does **not** substitute for lookup by retailer+sku from inbound links.

---

### 2.6 `price_snapshots` (append-only time series)

**Purpose:** Historical and “latest” price/MRP/stock signal from scrapers.

**Columns (from `PriceRepo`):** `id`, `product_id`, `retailer`, `price_paise`, `mrp_paise`, `in_stock`, `captured_at` (ISO text in practice).

| Needed? | Notes |
|--------|--------|
| **Yes** | Charts, “latest price”, and `last_scrape_at` when combined with `stock_state`. |
| **Heavy** | Every successful observation with price/MRP inserts a row — **growth is unbounded** without retention or aggregation. |

**Hot queries:**

- Latest row per `(product_id, retailer)`: `ORDER BY captured_at DESC` / `DISTINCT ON (product_id, retailer) … ORDER BY … captured_at DESC`.
- Series: `WHERE product_id = $1 [AND retailer = $2] AND captured_at >= $cutoff ORDER BY captured_at`.

**Indexes (strongly recommended):**

```text
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_price_snapshots_product_retailer_time
  ON price_snapshots (product_id, retailer, captured_at DESC);
```

Optional: **partition by month** on `captured_at` if the table exceeds tens of millions of rows.

**What might be “not needed” long term:** Storing **every** poll when nothing changed — optional **dedupe** (insert only when price, MRP, or stock changes) reduces size; trade-off is losing exact scrape cadence for analytics.

---

### 2.7 `stock_state` (current row per store)

**Purpose:** Latest known in/out stock and scrape freshness per `(product_id, retailer)`.

**Columns (from `StockRepo`):** `product_id`, `retailer`, `in_stock`, `last_changed_at`, `last_checked_at`; **UNIQUE(`product_id`, `retailer`)**.

| Needed? | Notes |
|--------|--------|
| **Yes** | Updated on **every** observation so “last check” exists even when no price snapshot is written. |
| Overlap with snapshots | `in_stock` is duplicated when a snapshot exists — **intentional**: stock row is the fallback signal path. |

**Indexes:** Unique constraint already backs point lookups. Batch queries use `unnest` join — same btree works.

---

### 2.8 `tracking_requests`

**Purpose:** User-submitted “please track this URL” workflow; admin approve/reject.

**Columns (from `TrackingRepo`):** `id`, `user_id`, `raw_url`, `normalized_retailer_hint`, `desired_product_name`, `note`, `status`, `admin_note`, `created_at`, `decided_at`, `decided_by`, `promoted_product_id`.

| Needed? | Notes |
|--------|--------|
| **Yes** for self-serve onboarding | `init_db.py` version references different columns — **migrate scripts** to match this repo. |

**Indexes:** `(user_id, created_at DESC)`, `(status, created_at DESC)`.

---

### 2.9 `app_users`

**Purpose:** Registered users; `email`, `password_hash`, `role`, `created_at`.

| Needed? | Notes |
|--------|--------|
| **Yes** for web auth | **UNIQUE(email)** + index for login lookup. |

---

### 2.10 Not in Postgres (by design)

| Store | Role |
|--------|------|
| **Deal dedup / cooldown** | `deal_store.py` — in-memory in current design; observability `deal_stats` is wired for future DB stats but empty unless extended. |
| **Platform YAML** | `platform.yaml` / `config.yaml` — channels, defaults, `platform_sources`; not tables. |

---

## 3. Fewer tables: JSON on one row, scrape time vs alert time

### 3.1 `last_scraped_at` / `last_checked_at` is not the same as “last alerted”

| Concept | Meaning | Good home today | If you consolidate |
|--------|---------|-----------------|---------------------|
| **Last scrape / last check** | “We successfully polled this listing at…” — health, UI “last signal”, per-store status. | `stock_state.last_checked_at` (+ snapshot `captured_at` when a price row exists). | One **`listing_state` JSONB** on `catalog_products` keyed by retailer, **or** a single denormalized **`last_scrape_at`** on the product row = `max` across retailers for **list-only** APIs (detail still needs per-retailer). |
| **Last alerted** | “We **sent** a notification for this rule at…” — spam control, cooldown, **survives process restart**. | **Not in DB today**; stock transitions use in-memory `_last_stock_state` in `RuleEngine` (lost on restart). | Add **`last_alerted_at`** (timestamptz, nullable) on **each rule row** (`catalog_rules`) or per-channel map in JSON — **does not replace** scrape timestamps. |

Alerts stay useful as **configuration** (what to fire on). **`last_alerted_at`** is optional **state** layered on top so you can debounce (“don’t ping more than once per N hours for this rule”) without conflating it with “when did we last scrape”.

---

### 3.2 What moves into JSONB on `catalog_products` vs what stays relational

| Artifact | Decision | Notes |
|----------|----------|--------|
| **`catalog_product_identifiers`** | **Keep table** | Link / ASIN / SKU resolution from **inbound** retailer+sku must stay index-friendly — do **not** fold into product JSON (see §2.5). |
| **`catalog_watches`** | **Replace with JSON** | Target: **`listings`** (or similar) JSONB: **`retailer → { url, poll_seconds?, last_scraped_at, … }`**. Minimum you asked for is **retailer → `last_scraped_at`**; the worker still needs **URL** (and poll interval) in that same map or it cannot poll. |
| **`stock_state`** | Optional follow-on | If `listings` already carries `last_scraped_at` and you store **`in_stock`** per retailer in the same JSON (or only in `price_snapshots` latest), you may drop `stock_state` **after** migrating writers — not required on day one of JSON listings. |
| **`catalog_product_alerts`** | JSON or merge with rules | Same as before; **merge with rules** when you can. |

**Do not** put **append-only price history** into a JSON column on the product row — keep **`price_snapshots`** separate.

---

### 3.3 Alerts / rules: one model + `last_alerted_at`

Reasonable end state:

1. **Single rule source** — Either only `catalog_rules`, or only JSON `rules` on the product, **not** both `catalog_product_alerts` and `catalog_rules` with overlapping meaning.
2. **Add `last_alerted_at`** on each rule (when you care about restart-safe debouncing). Stock rules can still compare `in_stock` from scrape state; `last_alerted_at` only answers “did we already spam for this transition recently?”.

`last_updated_at` on the product row is ambiguous (name edit? scrape? alert?) — prefer **explicit** names: `catalog_products.updated_at` for metadata edits, scrape times inside `listing_state` or `stock_state`, **`last_alerted_at` on rules**.

---

### 3.4 “Aggressive consolidation” blueprint (reference)

If the goal is **minimum table count** while staying sane:

| Table | Role |
|-------|------|
| **`catalog_products`** | Core fields + **`listings` JSONB** (`retailer` → url, `last_scraped_at`, optional stock fields). **No** identifiers blob here — keep **`catalog_product_identifiers`**. |
| **`catalog_product_identifiers`** | **Stay** — indexed `(retailer, sku)` for wishlist / link resolution. |
| **`price_snapshots`** | **Keep** — time series only here. |
| **`catalog_rules`** | One row per rule; add **`last_alerted_at`** when you need restart-safe debouncing; migrate away from `catalog_product_alerts` when possible. |
| **`app_users`**, **`tracking_requests`** | Keep only if those features stay on. |

Dropped when migrated: **`catalog_watches`** (into product JSON), optionally **`stock_state`** if listing JSON + snapshots cover your read paths.

Implementation = migration + repo rewrite (load merged config, poller, admin, APIs).

---

## 4. Earlier redundancy notes (unchanged ideas)

1. **`catalog_product_alerts` vs `catalog_rules`** — Still the main duplicate concept; consolidate into one model (above) when you can migrate admin flows.

2. **`in_stock` on both `price_snapshots` and `stock_state` / JSON listing** — Point-in-time history vs current operational signal; at most one “current” store if you collapse `stock_state` into JSON.

3. **TEXT timestamps** — Prefer **timestamptz** for `last_alerted_at` and scrape fields when you redesign.

---

## 5. Recommended optimisation checklist

- [ ] Apply **[`scripts/sql/recommended_indexes.sql`](../scripts/sql/recommended_indexes.sql)** per **§7.2** (identifiers; price_snapshots; product_alerts; watches; rules partial; tracking; users — verify duplicates / `enabled` column first).
- [ ] Refactor **`build_status_payload`** to use batch snapshot/stock reads (same pattern as `/api/products`).
- [ ] Define **retention** for `price_snapshots` (e.g. 90-day detail + monthly rollups) if insert volume is high.
- [ ] Replace or fix **`scripts/init_db.py`** to match production DDL (or adopt Alembic/sql migrations).
- [ ] Consider **`latest_listing`** (materialized view or table) updated on write if `DISTINCT ON` on a huge `price_snapshots` becomes slow — only if metrics show it.
- [ ] **Longer-term:** migrate **`catalog_watches` → `catalog_products.listings` JSONB** (`retailer` → url + `last_scraped_at`); add **`catalog_rules.last_alerted_at`**; keep **identifiers** as its own table.

---

## 6. Summary: what is essential (current code)

| Table | Essential for core product |
|-------|----------------------------|
| `catalog_products` | Yes — **target:** add `listings` JSONB; holds retailer → url + `last_scraped_at` (see §2.2, §3) |
| `catalog_watches` | Yes **today**; **remove after migration** to product `listings` JSON |
| `catalog_product_identifiers` | **Yes — keep table** for link/ASIN lookup; **not** JSON on product (§2.5) |
| `catalog_rules` | Yes if server notifications are used |
| `catalog_product_alerts` | Yes if you rely on DB-backed alert configs in overlay (candidate to merge with rules) |
| `price_snapshots` | Yes for history + priced latest signal — **do not fold into JSON** |
| `stock_state` | Yes for scrape heartbeat + stock without price today (optional once `listings` + snapshots cover reads) |
| `tracking_requests` | Only if user request workflow is enabled |
| `app_users` | Only if web auth is enabled |

This file is a living review: update it when migrations add columns or when observability/deals start persisting to Postgres.

---

## 7. DBA scrutiny (what is solid, what is wrong, what is missing)

This section **reviews the document and `recommended_indexes.sql` as artifacts** — not a substitute for `EXPLAIN (ANALYZE, BUFFERS)` on production data.

### 7.1 Factual / narrative corrections

| Topic | Issue |
|-------|--------|
| **§1.2 merged config** | Previously implied config stayed “in memory” across detail/status — **false** for current FastAPI handlers: **each request** reloads full merge unless you add caching or narrower queries. Text in §1.2 is corrected accordingly. |
| **`stock_state` “PK lookup”** | Doc referred loosely to PK; the code uses **`UNIQUE(product_id, retailer)`** conflict target. Functionally fine; wording should match actual constraint names in `pg_constraint`. |

### 7.2 `recommended_indexes.sql` — operational and DDL risks

| Risk | Detail |
|------|--------|
| **`CREATE INDEX CONCURRENTLY`** | In PostgreSQL, **`CONCURRENTLY` must not run inside a transaction block** (`BEGIN`…`COMMIT`). Many migration runners wrap files in a transaction — **each statement should be submitted alone** (e.g. psql one-by-one, or migration tool with autocommit per statement). |
| **Failure leaves INVALID index** | If `CONCURRENTLY` fails mid-build, you get an **invalid** index — must **`REINDEX INDEX CONCURRENTLY`** or **`DROP INDEX CONCURRENTLY`** and retry. Operators should know the playbook. |
| **`app_users (email)`** | If the table already has **`UNIQUE (email)`**, a second btree on `email` is **redundant** — check `pg_indexes` / `\d app_users` before applying. |
| **Dual indexes on `catalog_rules`** | Both `idx_catalog_rules_product_id` and partial `… WHERE enabled = true` on `(product_id)` overlap. For **`SELECT * FROM catalog_rules WHERE enabled = true`** (global rule load), a **single partial index** on `(product_id)` `WHERE enabled` is often enough; **drop the non-partial** duplicate unless you have hot queries that need disabled rows by `product_id`. Fewer indexes = faster writes. |
| **`catalog_rules.enabled`** | Partial index DDL **assumes the column exists**. Older hand-rolled DBs may lack it — verify before deploy. |
| **`created_at DESC` in index** | PostgreSQL **can** use btree with `DESC` for both “newest first per user” and backward scans; harmless if queries use `ORDER BY created_at` either direction. **Text / `timestamptz` typing**: if `created_at` is stored as **text** ISO strings, ordering still works lexically for ISO-8601-shaped values but is weaker for range logic than **`timestamptz`**. |

### 7.3 Gaps the document should not hide

| Gap | Why it matters |
|-----|----------------|
| **`catalog_product_alerts`** | Index **`(product_id, position)`** is now in `recommended_indexes.sql` — confirm it matches your live column list (`position` not null). |
| **Foreign keys** | Inventory lists logical parents/children but does not assert **enforced FKs** in the live DB (e.g. `price_snapshots.product_id` → `catalog_products.id`). Without FKs you keep orphans and hurt the planner’s ability to reason; with FKs you need indexes on the **referencing** side (often already covered). |
| **Autovacuum / bloat** | **`price_snapshots`** is append-heavy — monitor **dead tuples**, **autovacuum lag**, and **index bloat**. Retention (partition drop or `DELETE …`) must be paired with **`VACUUM`** strategy or you trade space for churn. |
| **Connection pool vs workers** | Many concurrent polls + web traffic share **`max_size=10`** in `Database.open` — not a schema topic, but a **latency** one: pool wait time shows up as “slow queries”. |
| **Replication / backup** | No RPO/RTO or read-replica strategy here — out of scope for app DDL, in scope for a real DBA runbook. |

### 7.4 What is already directionally correct

- **Batch** snapshot + stock for public list/status matches how to avoid N+1.
- **Identifiers `(retailer, sku)`** index matches the resolver access path.
- **`(product_id, retailer, captured_at)`** on `price_snapshots` supports both “latest per pair” (`DISTINCT ON` / backward scan) and “series in time order” for typical bounds queries.
- Calling out **`build_status_payload` N+1** and **`init_db.py` drift`** is honest technical debt marking.

### 7.5 Suggested verification commands (after index deploy)

Run on staging with realistic volumes: `EXPLAIN (ANALYZE, BUFFERS)` for (1) batch snapshot query, (2) `list_overlay` three-query sequence, (3) `list_price_series`, (4) identifier lookup by retailer+sku. Compare **shared hit** vs **read from disk** and **rows removed by filter** before/after indexes.
