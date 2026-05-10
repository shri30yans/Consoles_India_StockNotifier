# Deal Discovery Platform — agent context

Hermes should treat this repository as the **Deal Discovery Platform** (India retailers: Amazon.in, Flipkart, Ajio, Myntra). It scrapes deal surfaces, scores deals, stores state in PostgreSQL, and sends alerts (Telegram, Discord, X, HTTP).

## Working directory

Start Hermes from this **repository root** (the directory that contains `config.yaml` and `pyproject.toml`). Terminal tools, tests, and `python -m commerce_platform` assume that cwd.

If you use **Hermes Gateway** or scheduled jobs, point the gateway or job working directory at this same path so file and shell tools stay consistent.

## How to run the application

1. **Environment:** Copy `.env.example` to `.env` and set `DATABASE_URL` (PostgreSQL). Optional vars follow `.env.example` and `commerce_platform/platform/config/env.py`.
2. **One-time database:** `python scripts/init_db.py`
3. **Preflight:** `python verify_system.py`
4. **Full stack (recommended):** single process — HTTP API, static frontend, stock runner, deal discovery, observation pipeline:
   ```powershell
   python -m commerce_platform --host 0.0.0.0 --port 8000
   ```
5. **Split processes (debugging):**
   - API: `uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload`
   - Workers only: `python scripts/workers.py`

**Health:** `GET http://localhost:8000/api/health` or `http://localhost:8000/api/system`  
**UI:** `http://localhost:8000/deals` and `http://localhost:8000/admin`

## Architecture (short)

- **Entry:** `python -m commerce_platform` → FastAPI (`commerce_platform/web/main.py`) plus asyncio tasks from `commerce_platform/runtime/worker_bootstrap.py`.
- **Workers:** `commerce_platform/stock/runner.py` (scheduled polls + discovery), `commerce_platform/stock/deal_discovery_watcher.py` (listing scrapes), in-process **EventBus** for `PriceObservation` → **RuleEngine** → **ChannelRouter** / notifiers under `commerce_platform/platform/notify/`.
- **Fetching:** Playwright-backed fetcher in `commerce_platform/platform/fetch/` for rendered pages where needed.
- **Config:** `config.yaml` plus DB-backed tunables in `config_settings` (edit via admin API).

Design doc for consolidation and repo conventions: **`CLAUDE.md`** (read before substantive Python changes).

## Python environment

- Prefer the project venv and `pip install -r requirements.txt` or install via `pyproject.toml` as documented in README / QUICKSTART.
- **Windows:** `commerce_platform/__main__.py` sets `WindowsProactorEventLoopPolicy` for Playwright subprocess support — keep that when adding alternate entrypoints.

## Secrets and safety

- Never commit `.env` or paste secrets into chats or logs.
- Do not bulk-export database connection strings into untrusted channels.

## Tests

- Unit and integration tests live under `tests/`. Live retailer tests may fail when sites change markup; that is expected until parsers are updated.

## Frontend

- Production static assets are built into `commerce_platform/web/static/` and served by FastAPI. For active UI development, see `frontend/COMPLETE_SETUP.md`.
