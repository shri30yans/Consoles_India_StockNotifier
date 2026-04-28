"""Minimal in-page tweaks to reduce obvious headless automation signals."""

# Applied once per browser context. Sites differ; keep conservative.
PLAYWRIGHT_STEALTH_INIT = """
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined,
  configurable: true,
});
"""
