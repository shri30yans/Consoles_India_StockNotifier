---
name: redesign-service-architecture
description: Guides end-to-end redesign of a script-style service into layered modules, declarative config, and testable boundaries. Use when refactoring monoliths, moving to YAML/TOML config, splitting parsers from I/O, or when the user asks for senior-level architecture or “correct by design” refactors.
---

# Redesign service architecture (senior pass)

## Mental model

1. **Separate concerns by lifecycle**: configuration (pure data) → fetch (I/O) → parse (deterministic) → policy (dedupe / rate limits) → notify (side effects). Nothing that sends Telegram should parse HTML in the same function.
2. **One source of truth**: product URLs, headers, and job lists live in versioned config (YAML/JSON), not duplicated across `main.py` loops and Python dicts.
3. **Explicit contracts**: parsers return structured outcomes (e.g. `StockSignal` / `ParseResult`), not “call notify inside the parser.”
4. **Resource ownership**: one HTTP session per process; one browser context shared; one page per long-lived poll loop—close on shutdown.
5. **Fail closed**: missing product link, unknown site, or bad mode → log and skip, not half-register tasks.

## Redesign checklist

### Discovery (read-only)

- [ ] Map entrypoints, globals, and import cycles.
- [ ] List side effects (network, disk, notifications) and where they fire.
- [ ] Identify bugs from mixed concerns (e.g. tasks not gathered, wrong dict keys for state).

### Target shape

- [ ] **Config layer**: `app.*` (flags, paths), `products.*`, `websites/<site>.yaml`, `jobs.yaml` (transport + product + site + delay).
- [ ] **Domain types**: small frozen dataclasses for Product, Website, Job, ParseResult.
- [ ] **Fetch layer**: `AiohttpFetcher` / `PlaywrightFetcher` only return HTML (and optional page handle for screenshots).
- [ ] **Parsers**: one module per supported retailer; `registry.py` dispatches on `website_key`; supported set matches `jobs.yaml` validation (this repo: **amazon**, **flipkart** only).
- [ ] **State**: a class wrapping the former global dict (naming fixed: `continuous` not `countinous`).
- [ ] **Notifications**: single service consuming signals + state; secrets from `os.environ` / `.env`, never committed.
- [ ] **Runner**: builds `asyncio.Task` list from jobs file; `gather`; `try/finally` closes fetchers.

### Validation

- [ ] Import smoke: `python -c "from stock_notifier.config_loader import load_products"`.
- [ ] Mode `pause` yields zero tasks without error.
- [ ] Dry-run option (optional): parsers only, no HTTP.

## Anti-patterns to remove

- Global `tasks` list mutated across functions; nested `create_task(create_task(...))`.
- New `ClientSession` per request in a hot loop.
- Parsers calling `notify()` directly.
- Config split across three Python mega-files with Discord IDs next to scraper headers.

## When editing this codebase

- Add retailers under `stock_notifier/parsers/<site>.py` and register in `registry.py`.
- Add headers or wishlist ASINs under `config/websites/<site>.yaml`.
- Add or remove monitors only in `config/jobs.yaml`.

## Reference layout (this repo)

```
config/
  app.yaml
  jobs.yaml
  products.yaml
  websites/
    amazon.yaml
    flipkart.yaml
stock_notifier/
  retailers.py          # PARSER_SUPPORTED_WEBSITE_KEYS — single source for “has parser”
  config_loader.py
  config_validation.py  # product + URL checks for each job
  models.py
  runner.py
  fetch/
  parsers/              # amazon.py, flipkart.py, registry.py
  notify/
  stock_state.py
```
