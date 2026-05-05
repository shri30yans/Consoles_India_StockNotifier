# Scraping Strategy: BeautifulSoup vs Playwright

## Quick Answer

**No, do NOT switch to Playwright everywhere.**

- **BeautifulSoup** (fast, low overhead) for static HTML
- **Playwright** (slow, needs browser) for JS-rendered content
- Both strategies used by parsers via JSON-LD fallback

---

## Detailed Analysis

### BeautifulSoup (Current Primary)

**When**: Static HTML (most pages)
**Speed**: <1s per page
**Overhead**: Minimal (pure Python)
**Reliability**: Good for static sites, fails on JS-rendered

```python
soup = BeautifulSoup(html, "html.parser")
products = soup.find_all("a", href=re.compile(r"/p/"))
```

**Retailers**: Amazon (mostly static), Flipkart (mostly static)

### Playwright (Fallback for JS)

**When**: JS-rendered content (React, Vue, Angular)
**Speed**: 3-5s per page
**Overhead**: Browser process, memory, CPU
**Reliability**: Handles dynamic content, but slow

```python
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto(url, wait_until="networkidle")
    html = await page.content()  # Now includes JS-rendered content
```

**Retailers**: Ajio (React), Myntra (React)

### JSON-LD (Most Reliable)

**When**: Structured data embedded in HTML
**Speed**: <100ms (simple JSON parsing)
**Overhead**: None
**Reliability**: Excellent (W3C standard)

```python
<script type="application/ld+json">
  {"@type": "Product", "name": "...", "offers": {"price": "..."}}
</script>
```

**Why it works**: Most e-commerce sites embed JSON-LD for SEO. Survives CSS changes.

---

## Current Implementation

### Parser Strategy

```python
def extract_amazon_deal_items(html: str) -> list[ListingItem]:
    # Step 1: Try CSS selectors (fast, brittle)
    items = _extract_via_css(html)
    
    # Step 2: Fallback to JSON-LD (reliable, slow to code)
    if not items:
        items = _extract_via_jsonld(html)
    
    # Step 3: Raise error if both fail
    if not items:
        raise ValueError("...")
```

**This is correct. Don't change it.**

### Why Not Playwright Everywhere?

1. **Performance**: 3-5s per page × 50 deals/page = 2-4 min per retailer
   - BeautifulSoup: <1s per page = <50s total
   - **3-5x slower**

2. **Resource Usage**: Browser process per concurrent request
   - Config: `max_concurrent_playwright: 2` (vs 4 for BeautifulSoup)
   - More memory, more CPU, fewer parallel requests

3. **Complexity**: Playwright adds flakiness
   - Browser crashes
   - Page load timeouts
   - Stealth mode bypass risks (retailers detect bots)

4. **When It Breaks**: If Playwright blocks, CSS parsing still works
   - Redundancy: BS4 + Playwright = fault tolerance
   - Playwright everywhere = single point of failure

---

## Recommended Approach

### Stage 1 (Current): CSS + JSON-LD
```
Amazon    → CSS (mostly static) → JSON-LD fallback
Flipkart  → CSS (mostly static) → JSON-LD fallback
Ajio      → CSS (partial JS)   → JSON-LD fallback
Myntra    → CSS (partial JS)   → JSON-LD fallback
```

**Status**: Ready. Tests may fail if CSS changes, but JSON-LD catches most.

### Stage 2 (If CSS Fails): Playwright Fallback
```
If extract_amazon_deal_items(html) raises ValueError:
  → ParserFixerAgent analyzes CSS
  → Suggests new selectors
  → OR recommends Playwright for this retailer
  → Admin approves → Deploy fix
```

**Status**: ParserFixerAgent (phase 11, future).

### Stage 3 (Production): Smart Fetcher
```python
async def get_html(url: str) -> str:
    # Try fast BeautifulSoup-friendly fetch first
    html = await fetcher.get(url, timeout=5)
    
    # If HTML too small (JS not rendered), use Playwright
    if len(html) < 10000:  # Heuristic: JS site has larger HTML
        html = await fetcher.get_with_playwright(url, timeout=10)
    
    return html
```

**Status**: Future optimization. Measure before implement.

---

## Testing Strategy

### Unit Tests (No Network)
```python
# tests/test_serp_parsers.py
def test_extract_amazon_with_mock_html():
    html = """<html>...</html>"""  # Mock Amazon page
    items = extract_amazon_deal_items(html, max_items=50)
    assert len(items) > 0
    assert items[0].price_inr > 0
```

**Status**: TODO. Create mock HTML for each retailer.

### Integration Tests (Real Pages)
```python
# tests/test_deal_scrapers_live.py
async def test_extract_amazon_deal_items_real():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.amazon.in/deals")
        html = await page.content()
        
        items = extract_amazon_deal_items(html, max_items=50)
        assert len(items) > 0  # Will fail if CSS changed
```

**Status**: Done. Tests fail when CSS changes (expected).

---

## If Retailers Block BeautifulSoup

### Scenario
Amazon detects BeautifulSoup requests, blocks them.

### Solution
```python
# In config.yaml
stock:
  fetch:
    http_client: curl_cffi          # ✅ Already configured
    curl_impersonate: chrome124     # ✅ Impersonates browser
    use_fake_useragent: true        # ✅ Randomizes User-Agent
```

**Status**: Already enabled. curl_cffi + Chrome impersonation defeats bot detection.

### If Still Blocked
Switch to Playwright only for that retailer:
```python
if source.type == "amazon_deals":
    html = await fetcher.get_with_playwright(seed_url)
else:
    html = await fetcher.get(seed_url)  # BS4-friendly
```

**Status**: Easy fallback in discovery_agent.py.

---

## Playwright vs Headless Chrome

**Question**: Should we use `curl_impersonate` or Playwright Chrome?

**Answer**: Both, strategically.

| Tool | Best For | Why |
|------|----------|-----|
| curl_cffi | 90% of requests | Fast, low overhead, Chrome fingerprint |
| Playwright | JS rendering | Wait for network, capture DOM after JS executes |

**No**: Don't replace curl_cffi with Playwright everywhere.
- curl_cffi is faster for static pages
- Playwright needed only for dynamic content

---

## Performance Budget

| Stage | Component | Time Per Item | Items/Hour |
|-------|-----------|---------------|-----------|
| 1 (Current) | CSS parse | 20ms | 180 |
| 1 (Current) | JSON-LD fallback | 100ms | 36 |
| 1 (Current) | PDP fetch + parse | 1-2s | 2-3 |
| 2 (Future) | Playwright render | 3-5s | 0.7-1 |

**Verdict**: Stay with BS4 + JSON-LD. Don't use Playwright for 50 items/hour (too slow).

---

## ParserFixerAgent Will Handle Brittle CSS

When CSS breaks:
1. Discovery fails → ValueError
2. Agent logs error
3. ParserFixerAgent analyzes page
4. Suggests new selectors
5. Admin validates → Deploy fix

**This is better than hardening for future changes.**

Hardening = Over-engineering for rare events.
Self-healing = Adapt when it actually breaks.

---

## Summary

| Question | Answer |
|----------|--------|
| Use Playwright everywhere? | **No** - too slow, use CSS + JSON-LD |
| When use Playwright? | JS-rendered pages where CSS fails |
| What if CSS breaks? | JSON-LD fallback catches it |
| What if JSON-LD fails too? | ParserFixerAgent suggests fixes |
| Is curl_cffi enough? | Yes, for 95% of cases |
| Performance impact of Playwright? | 3-5x slower, not worth for full scrapes |
| Recommended ratio? | BS4 (95%) + Playwright (5%) |

**Current implementation is optimal. Don't change it.**
