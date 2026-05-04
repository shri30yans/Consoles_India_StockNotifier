-- Recommended indexes for commerce_platform query patterns.
-- Run against your Postgres (Supabase, etc.) as a superuser or owner.
--
-- DBA notes:
--   • CREATE INDEX CONCURRENTLY cannot run inside a transaction block — run each
--     statement outside BEGIN/COMMIT, or use a runner that autocommits per statement.
--   • On failure, you may have an INVALID index — REINDEX INDEX CONCURRENTLY or DROP
--     and recreate.
--   • Inspect pg_indexes before creating idx_app_users_email — skip if UNIQUE(email)
--     already exists (duplicate btree).

-- ---------------------------------------------------------------------------
-- catalog_product_identifiers
-- Hot path: wishlist / link resolution — WHERE retailer = $1 AND sku = $2
-- Keep this TABLE (not JSON on product) so lookups stay index-friendly and
-- you can join from arbitrary product URLs / ASINs without scanning products.
-- ---------------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_catalog_product_identifiers_retailer_sku
  ON catalog_product_identifiers (retailer, sku);

-- ---------------------------------------------------------------------------
-- price_snapshots
-- Hot paths: latest row per (product_id, retailer); time-range series.
-- ---------------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_price_snapshots_product_retailer_captured
  ON price_snapshots (product_id, retailer, captured_at DESC);

-- ---------------------------------------------------------------------------
-- catalog_product_alerts
-- Hot path: list_overlay — WHERE product_id = ? ORDER BY position
-- ---------------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_catalog_product_alerts_product_position
  ON catalog_product_alerts (product_id, position);

-- ---------------------------------------------------------------------------
-- catalog_watches
-- Hot path: WHERE product_id = $1 (until watches migrate to product JSON).
-- ---------------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_catalog_watches_product_id
  ON catalog_watches (product_id);

-- ---------------------------------------------------------------------------
-- catalog_rules
-- Hot path: RuleEngine loads all rows WHERE enabled = true (no product filter).
-- One partial index avoids duplicating btree write cost vs a second non-partial
-- index on product_id. Requires column "enabled" on catalog_rules.
-- ---------------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_catalog_rules_enabled_product
  ON catalog_rules (product_id)
  WHERE enabled = true;

-- ---------------------------------------------------------------------------
-- tracking_requests
-- ---------------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tracking_requests_user_created
  ON tracking_requests (user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tracking_requests_status_created
  ON tracking_requests (status, created_at DESC);

-- ---------------------------------------------------------------------------
-- app_users
-- Hot path: WHERE email = $1 (emails are normalized to lower case on insert).
-- Skip if you already have UNIQUE(email) — btree for login is enough.
-- ---------------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_app_users_email
  ON app_users (email);
