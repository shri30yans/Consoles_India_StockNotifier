# Commerce Platform — Stock Notifier & Deals Aggregator

A unified platform for real-time stock monitoring, price tracking, and deal aggregation across Indian e-commerce retailers (Amazon, Flipkart, etc.). Built with **Python async backend** + **React TypeScript frontend**.

## What It Does

- 🎮 **Stock Alerts** — Real-time monitoring of product availability on multiple retailers
- 💰 **Price Tracking** — Historical price snapshots with trend analysis
- 🤖 **Deals Aggregation** — Scrape and score deals from aggregators (DesiDime, Reddit)
- 🔔 **Multi-Channel Notifications** — Push alerts via Telegram, Discord, Email
- 📊 **Web Dashboard** — React frontend for managing products, rules, and viewing alerts

## Architecture

```
backend/
├── commerce_platform/          # Main Python application
│   ├── stock/                  # Stock polling & wishlist watching
│   ├── deals/                  # Deal aggregation & scoring
│   ├── platform/               # Core: config, logging, database
│   ├── rules/                  # Alert rule engine
│   ├── notify/                 # Notification channels
│   └── web/                    # FastAPI HTTP API
├── bot.py                      # Entry point (Procfile/Docker)
├── init_db.py                  # Database schema initialization
├── platform.yaml               # Application configuration
└── requirements.txt            # Python dependencies

frontend/
├── src/                        # React + TypeScript source
├── public/                     # Static assets
├── vite.config.ts             # Build configuration
└── package.json               # Node dependencies
```

## Quick Start

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **PostgreSQL** (Supabase recommended for managed hosting)
- **Telegram Bot Token** (for notifications)

### 1. Backend Setup

```bash
# Clone repo & create virtual environment
git clone <repo>
cd C--Programs-Consoles-India-StockNotifier
python -m venv venv
venv\Scripts\activate  # Windows: use .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Telegram token, database URL, etc.

# Initialize database
python init_db.py

# Start backend (API + workers)
python bot.py
# OR with custom port/config:
python bot.py --config platform.yaml --port 8000 --host 127.0.0.1
```

**Backend will start:**
- FastAPI HTTP server on `http://127.0.0.1:8000`
- Stock polling workers (background)
- Deal aggregation workers (background)

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (with HMR)
npm run dev
# Opens at http://localhost:5173

# Build for production
npm run build
# Output in frontend/dist/
```

### 3. Access the Application

- **Backend API:** http://127.0.0.1:8000
- **Frontend:** http://localhost:5173 (dev) or http://127.0.0.1:8000 (production)
- **API Docs:** http://127.0.0.1:8000/docs (Swagger)

## Configuration

### Platform Config (`platform.yaml`)

Core application settings:

```yaml
platform:
  store:
    dsn: null  # Uses DATABASE_URL env var if null
  log_level: DEBUG
  config_reload_seconds: 60

channels:
  - id: gaming_alerts
    name: Gaming Stock Alerts
    telegram:
      chat_id: env:TELEGRAM_GAMING_CHAT_ID

defaults:
  poll_seconds: 60
  alerts:
    - type: back_in_stock
      channels: [gaming_alerts]

products: []  # Load from DB overlay or seed from YAML

platform_sources:
  - type: amazon_wishlist
    url: https://www.amazon.in/hz/wishlist/ls/YOUR_ID
    channels: [gaming_alerts]
    poll_seconds: 20
```

See `platform.yaml.example` for all options.

### Environment Variables (`.env`)

```bash
# Telegram
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_ADMIN_CHAT=your_chat_id
TELEGRAM_GAMING_CHAT_ID=your_chat_id
TELEGRAM_DEALS_GAMING_CHAT_ID=your_chat_id

# Database (Supabase Postgres)
DATABASE_URL=postgresql://user:password@host:5432/postgres

# API
WEB_JWT_SECRET=your_secret_key

# Optional: LLM for deal curation
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-2.0-flash

# Optional: Reddit aggregator
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
```

## Deployment

### Docker (Recommended)

```bash
# Build image
docker build -t commerce-platform .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e TELEGRAM_TOKEN="..." \
  --env-file .env \
  commerce-platform
```

### Docker Compose

```bash
docker-compose up -d
```

See `docker-compose.yml` for full setup.

### Heroku / Railway / Render

```bash
# Procfile already configured
# Deploy with:
git push heroku main
```

### Systemd (Linux)

```bash
# Copy service file
sudo cp deploy/commerce-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable commerce-web
sudo systemctl start commerce-web
```

### Frontend Deployment

Build and serve static files:

```bash
cd frontend
npm run build  # Creates dist/ folder

# Serve with Python backend (auto-configured)
# OR use any static host (Vercel, Netlify, S3 + CloudFront)
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/

# With coverage
pytest --cov=commerce_platform tests/
```

### Code Quality

```bash
# Linting
ruff check commerce_platform/

# Type checking
mypy commerce_platform/

# Format
ruff format commerce_platform/
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Manual run
pre-commit run --all-files
```

## Database Schema

Initialized by `init_db.py`. Tables:

- `catalog_products` — Product definitions
- `catalog_watches` — URLs to monitor
- `catalog_product_alerts` — Alert rules
- `catalog_product_identifiers` — Retailer SKUs (ASIN, etc.)
- `catalog_rules` — Notification rules
- `price_snapshots` — Historical pricing
- `stock_state` — Current inventory status
- `tracking_requests` — User-created watches

## Scripts

Utility scripts in `scripts/`:

- `import_catalog_from_yaml.py` — Bulk import products from YAML seed file
- `telegram_resolve_chat_id.py` — Get your Telegram chat ID
- `scrape_debug.py` — Test scraper against URL
- `amazon_search_page_extract.js` — Extract Amazon search results

```bash
python scripts/import_catalog_from_yaml.py --config products.yaml
python scripts/telegram_resolve_chat_id.py
```

## Troubleshooting

### Database Connection Issues

```
UndefinedTableError: relation "catalog_X" does not exist
```

Run schema initialization:

```bash
python init_db.py
```

### Telegram Not Sending

1. Verify `TELEGRAM_TOKEN` is valid
2. Check `TELEGRAM_ADMIN_CHAT` is correct
3. Test with: `python scripts/telegram_resolve_chat_id.py`

### Frontend Won't Connect to Backend

1. Ensure backend is running on correct host/port
2. Check `.env` for `WEB_CORS_ORIGINS` (should include frontend URL)
3. Backend logs should show CORS errors

### Wishlist Returns 0 Items

Amazon login may be required. Check platform.yaml `url` and ensure wishlist is public.

## Tech Stack

**Backend:**
- Python 3.10+ with async/await (asyncio)
- FastAPI — HTTP API
- asyncpg — Postgres driver
- curl-cffi / playwright — Headless browser scraping
- Telegram / Discord / Email — Notification channels

**Frontend:**
- React 19 + TypeScript
- Vite — Build tool
- TailwindCSS — Styling
- Shadcn — UI components
- React Router — Navigation

**Infrastructure:**
- PostgreSQL (Supabase)
- Docker / Docker Compose
- Systemd / Heroku / Railway

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

[Specify your license]

## Support

- **Issues:** File on GitHub
- **Email:** shri30yans@gmail.com
