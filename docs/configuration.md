# Configuration reference

## Layout

| Path | Purpose |
|------|---------|
| `config/app.yaml` | Feature flags, logging, fetch tuning, affiliate tag default |
| `config/jobs.yaml` | Which products to poll, transport, interval |
| `config/products/<KEY>.yaml` | One file per product (`key` must match filename stem) |
| `config/websites/amazon.yaml` | Amazon headers, wishlist ASIN map |
| `config/websites/flipkart.yaml` | Flipkart headers |

Override the config root with environment variable `STOCK_NOTIFIER_CONFIG_DIR` (absolute or relative path).

## `config/app.yaml`

- **`notify`**: When false, stock transitions are tracked but Telegram/Twitter are not called.
- **`mode`**: `requests`, `playwright`, `all`, or `pause`.
- **`amazon_affiliate_tag`**: Default tag in product URLs; overridden by `AMAZON_AFFILIATE_TAG` if that env var is non-empty.
- **`telegram_chat_id`**: Channel or `@username` for Telegram.
- **`paths.logs_dir`**: Directory for `stock_notifier.log` (under the repo root unless you use an absolute path elsewhere).
- **`logging.json_lines`**: When true, file + console logs are JSON lines (also set `LOG_JSON=true` in the environment to force JSON on).
- **`logging.max_bytes`** / **`logging.backup_count`**: `RotatingFileHandler` rotation for the log file.
- **`fetch.jitter_max_seconds`**: Extra random delay uniform in `[0, value]` added after each poll sleep (reduces synchronized wakeups).
- **`fetch.max_concurrent_per_transport`**: Cap concurrent HTTP or Playwright fetches per transport (`0` = unlimited).
- **`fetch.use_fake_useragent`**: When true, [`fake-useragent`](https://pypi.org/project/fake-useragent/) supplies rotating `User-Agent` strings (YAML header pools are still merged; the UA field is replaced each request unless this is false).
- **`fetch.http_client`**: `aiohttp` (default) or `curl_cffi`. Use **`curl_cffi`** when retailers block plain aiohttp TLS fingerprints; set **`fetch.curl_impersonate`** to a profile supported by your `curl_cffi` build (e.g. `chrome124`, `chrome120`, `safari17_0`).
- **`fetch.playwright_apply_stealth`**: Enables a small `navigator.webdriver` init script, `AutomationControlled` blink flag off, and India-like **`playwright_locale`** / **`playwright_timezone_id`** on the shared browser context. Not a guarantee against bot systems—re-test when a site changes detection.

## Secrets (environment / `.env`)

Never commit `.env`. Supported variables:

| Variable | Used for |
|----------|----------|
| `TELEGRAM_TOKEN` | Telegram Bot API |
| `consumer_key`, `consumer_secret`, `access_token`, `access_token_secret` | Twitter / X posting |
| `AMAZON_AFFILIATE_TAG` | Overrides `amazon_affiliate_tag` from YAML when set |
| `LOG_JSON` | If `true` / `1` / `yes`, forces JSON logging regardless of YAML |

## Graceful shutdown

On POSIX, `SIGINT` and `SIGTERM` cancel monitoring tasks and close the aiohttp session and Playwright browser. On Windows, `SIGINT` (Ctrl+C) is handled by the interpreter; `SIGTERM` may not be wired the same way.

## Running tests locally

If `pytest` fails during collection because of an unrelated globally installed plugin, run:

```text
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
pytest
```

## Adding a product

1. Copy an existing file under `config/products/` and edit fields.
2. Ensure `key` matches the filename stem (e.g. `PS5.yaml` → `key: PS5`).
3. Add jobs in `config/jobs.yaml` only for **amazon** or **flipkart** (the only parsers shipped).
