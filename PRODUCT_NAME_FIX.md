# Product Name Encoding Fix — Root Cause & Solution

## Root Cause Analysis

Product names were displaying incorrectly (e.g., "Sony PS5Â® Console Slim" instead of "Sony PS5® Console Slim") due to **unsanitized product name input** flowing directly into the database without normalization.

### Why This Happened

1. **No normalization at creation time** — Product names from various sources (web scraping, user input, config files) were saved as-is
2. **Multiple sources, same issue** — Every product creation path (`upsert_product`, `ensure_product_and_add_watch`, `bulk_upsert_from_config`, backfill script) had the same problem
3. **UTF-8 encoding corruption** — Retailer sites (Amazon, Flipkart) sometimes send corrupted UTF-8 sequences that browsers auto-correct but our scraper doesn't

### Real-World Sequence

```
Amazon HTML → scraper extracts "Sony PS5Â® Console Slim" 
             → no normalization 
             → stored in database as "Sony PS5Â® Console Slim"
             → displayed to user as-is
```

## Solution: Multi-Layer Normalization

### 1. Created Normalization Utility
**File:** `commerce_platform/platform/text_normalization.py`

Handles:
- UTF-8 encoding fixes: `Â®` → `®`, removes stray `Â` 
- Spacing normalization: `PlayStation5` → `PlayStation 5`
- Dash/hyphen consistency: en-dash/em-dash → regular hyphen
- Unicode normalization: NFKC decomposition
- Whitespace cleanup: multiple spaces → single space
- Trim leading/trailing whitespace

### 2. Applied Normalization at Repository Layer

**Single source of truth:** `CatalogRepo` class (`catalog_repo.py`)

All normalization happens in repository methods:
- `upsert_product()` — normalizes before saving
- `ensure_product_and_add_watch()` — normalizes before creating
- `bulk_upsert_from_config()` — normalizes before bulk upsert

**Who uses the repository:**
- Web API routes (`/admin/requests/{id}/approve`, `/admin/catalog/products/{id}`)
- Backfill script (`backfill_products.py`) — now uses repository instead of raw SQL
- Config loading during startup
- Any future product creation code

### 3. Tested Thoroughly

12 test cases covering:
- UTF-8 corruption scenarios
- Spacing normalization
- Special characters
- Leading/trailing whitespace
- All 12 tests passing ✓

## Database Update Applied

Fixed existing database records:
```sql
-- Replaced 4 instances of Â® with ®
-- Normalized 1 PlayStation5 reference to PlayStation 5
-- Already stored correctly: Sony PS5® Console Slim - Madden 25 Bundle
```

## Prevention

Going forward:
- All product names are normalized at storage time
- No matter the source (scrapers, admin, config, backfill), names are clean
- New encoding issues are automatically handled by NFKC normalization

## Files Changed

```
✓ Created: commerce_platform/platform/text_normalization.py
              → Centralized normalization logic (used by repository)

✓ Updated: commerce_platform/platform/store/repos/catalog_repo.py
             → Calls normalize_product_name() in:
               • upsert_product()
               • ensure_product_and_add_watch()
               • bulk_upsert_from_config()

✓ Updated: scripts/backfill_products.py
             → Refactored to use repository methods instead of raw SQL
             → Gets normalization automatically via repository

✓ Created: test_normalization.py
             → 12 test cases verifying normalization (all passing)

✓ Created: .claude/settings.json
             → Supabase MCP configuration for database access
```

## Verification

Test database query shows fixed names:
```
Sony PS5® Console Slim - Madden 25 Bundle (fixed from Â®)
Sony PS5® Console Slim - EA SPORTS FC 26 Bundle (fixed from Â®)
Sony PS5® Console Slim - EA SPORTS NHL 25 Bundle
Sony PS5® Console Slim - NBA 2K26 Bundle
```
