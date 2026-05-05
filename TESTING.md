# Testing Guide — Deal Discovery Platform

## Quick Start

```bash
# 1. Install test dependencies
pip install pytest pytest-asyncio playwright

# 2. Install browser binaries for Playwright
playwright install chromium

# 3. Run all tests
pytest tests/ -v

# 4. Run only live scraper tests (actually fetch from real sites)
pytest tests/test_deal_scrapers_live.py -v -s

# 5. Run specific retailer test
pytest tests/test_deal_scrapers_live.py::TestAmazonDealsScraper::test_extract_amazon_deal_items_real -v -s
```

## Test Organization

### Unit Tests
- `tests/test_parser_registry.py` — parser registration and type safety
- `tests/test_serp_parsers.py` — parser logic on mock HTML (no network)

### Integration Tests (Live Scraping)
- `tests/test_deal_scrapers_live.py` — fetch real retailer deal pages using Playwright

### Endpoint Tests
- `tests/test_admin_deals_api.py` — admin config endpoints (coming next)

## Live Scraper Tests

These tests use **Playwright** to render and scrape real retailer pages:

```
TestAmazonDealsScraper:
  ✓ test_extract_amazon_deal_items_real — Fetch amazon.in/deals, extract ≥1 item
  ✓ test_amazon_items_have_prices — Verify prices are extracted

TestFlipkartOffersScraper:
  ✓ test_extract_flipkart_offer_items_real — Fetch flipkart.com/offers, extract ≥1 item
  ✓ test_flipkart_items_have_prices — Verify prices are extracted

TestAjioOffersScraper:
  ✓ test_extract_ajio_offer_items_real — Fetch ajio.com/s/sale, extract ≥1 item

TestMyntraOffersScraper:
  ✓ test_extract_myntra_offer_items_real — Fetch myntra.com/offers, extract ≥1 item
```

### Why Playwright?

- **JS Rendering**: Ajio and Myntra use React. BeautifulSoup can't parse before JS executes.
- **Real-world**: Tests use actual site pages, not mocked HTML. Catches parser breakage immediately.
- **Headless**: Tests run without UI (`.launch(headless=True)`).

### Running Tests with Logging

```bash
# Show all debug logs (network requests, extraction details)
pytest tests/test_deal_scrapers_live.py -v -s --log-cli-level=DEBUG

# Capture output to file
pytest tests/test_deal_scrapers_live.py -v -s --log-file=test.log

# Run one test, stop on first failure
pytest tests/test_deal_scrapers_live.py::TestAmazonDealsScraper::test_extract_amazon_deal_items_real -x -v -s
```

## Expected Output

When tests pass, you'll see:

```
tests/test_deal_scrapers_live.py::TestAmazonDealsScraper::test_extract_amazon_deal_items_real PASSED
  Fetching Amazon deals page...
  Page loaded, HTML length: 287453
  Extracted 23 items
    PS5: ₹39999 (MRP ₹59990) 33% off
    iPhone 15: ₹79999 (MRP ₹89999) 11% off
    ...

tests/test_deal_scrapers_live.py::TestAmazonDealsScraper::test_amazon_items_have_prices PASSED
  Items with prices: 18/23

====== 8 passed in 45.23s ======
```

## Debugging Parser Failures

If a test fails with `ValueError("Amazon deals parser: Failed to extract any items...")`:

1. **Check site structure** — Retailer updated CSS classes
2. **Enable Playwright Inspector**:
   ```python
   # Add to test code:
   await page.pause()  # Opens browser inspector
   # Inspect element, note class names, update selectors
   ```
3. **Compare live vs test HTML** — Save page HTML and inspect in editor
4. **Update selector regex** in `serp_parsers.py`, then re-run test

## CI/CD Integration

For GitHub Actions, add to `.github/workflows/test.yml`:

```yaml
- name: Install Playwright browsers
  run: playwright install chromium

- name: Run live scraper tests
  run: pytest tests/test_deal_scrapers_live.py -v

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: test-logs
    path: test.log
```

## Troubleshooting

### Playwright not installed
```
pytest.skip: playwright not installed. Install with: pip install playwright
```

**Fix**: `pip install playwright && playwright install chromium`

### Timeout (30000ms)
If a page takes >30s to load, increase timeout:
```python
await page.goto(url, timeout=60000)  # 60 seconds
```

### CORS/Bot blocks
- Tests use real user agents via `curl_cffi` in fetch config
- If blocked, Playwright will pause with timeout
- Add delay: `await page.wait_for_timeout(2000)`

### Out of memory (many tests)
Run tests sequentially instead of in parallel:
```bash
pytest tests/test_deal_scrapers_live.py -v -n 1  # single worker
```

## Manual Testing

To manually test a parser:

```python
import asyncio
from playwright.async_api import async_playwright
from commerce_platform.stock.sources.serp_parsers import extract_amazon_deal_items

async def manual_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.amazon.in/deals", wait_until="networkidle")
        html = await page.content()
        
        items = extract_amazon_deal_items(html, max_items=50)
        for item in items[:5]:
            print(f"{item.title}: ₹{item.price_inr} ({item.discount_pct*100:.0f}% off)")
        
        await browser.close()

asyncio.run(manual_test())
```

## Next: Approval Workflow Tests

Once admin approval workflow is implemented, add:
- `test_deal_discovery_sends_to_admin.py` — watcher finds deal → sends to admin channel
- `test_admin_approves_deal.py` — admin approves → deal goes to users
- `test_deal_dedup_by_product_id.py` — same product via multiple sources → merged row
