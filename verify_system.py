#!/usr/bin/env python3
"""Comprehensive system health verification before startup."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv(Path('.env'), override=True)

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

checks_passed = 0
checks_failed = 0

def check_pass(msg: str):
    global checks_passed
    checks_passed += 1
    print(f"{GREEN}[PASS]{RESET}: {msg}")

def check_fail(msg: str):
    global checks_failed
    checks_failed += 1
    print(f"{RED}[FAIL]{RESET}: {msg}")

def check_warn(msg: str):
    print(f"{YELLOW}[WARN]{RESET}: {msg}")

def section(title: str):
    print(f"\n{CYAN}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{RESET}\n")

async def main():
    section("Environment & Config")

    # 1. Check .env
    if Path('.env').exists():
        check_pass(".env file exists")
    else:
        check_fail(".env file not found")
        return

    # 2. Check env vars
    db_url = os.getenv('DATABASE_URL', '').strip()
    if db_url and 'postgresql' in db_url:
        check_pass(f"DATABASE_URL configured ({db_url[:50]}...)")
    else:
        check_fail("DATABASE_URL not set or invalid")
        return

    db_ssl = os.getenv('DATABASE_SSL', 'true').lower()
    if db_ssl in ('true', 'false'):
        check_pass(f"DATABASE_SSL = {db_ssl}")
    else:
        check_fail(f"DATABASE_SSL invalid: {db_ssl}")

    # 3. Check config.yaml
    if Path('config.yaml').exists():
        check_pass("config.yaml exists")
    else:
        check_fail("config.yaml not found")
        return

    try:
        from commerce_platform.platform.config.loader import load
        config = load(Path('config.yaml'))
        check_pass(f"config.yaml loads: {len(config.platform_sources)} sources defined")
    except Exception as e:
        check_fail(f"config.yaml load error: {e}")
        return

    section("Python Dependencies")

    # 4. Check imports
    modules = [
        ('FastAPI', 'fastapi'),
        ('Pydantic', 'pydantic'),
        ('AsyncPG', 'asyncpg'),
        ('BeautifulSoup4', 'bs4'),
        ('Playwright', 'playwright'),
        ('python-dotenv', 'dotenv'),
    ]

    for name, module in modules:
        try:
            __import__(module)
            check_pass(f"{name} installed")
        except ImportError:
            check_fail(f"{name} not installed: pip install {module}")

    section("Application Modules")

    # 5. Check app can be imported
    try:
        from commerce_platform.web.main import create_app
        from commerce_platform.web.config import load_web_config
        check_pass("FastAPI app can be imported")
    except Exception as e:
        check_fail(f"Cannot import FastAPI app: {e}")
        return

    try:
        from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers
        check_pass("Worker bootstrap can be imported")
    except Exception as e:
        check_fail(f"Cannot import worker bootstrap: {e}")
        return

    section("Database Connection")

    # 6. Test database connection
    try:
        from commerce_platform.platform.store.db import Database
        db = Database(config.platform.store)
        await db.open()

        result = await db.pool.fetchval('SELECT 1')
        if result == 1:
            check_pass("PostgreSQL connection works")
        else:
            check_fail("PostgreSQL query returned unexpected result")
            await db.close()
            return

        # Check tables
        tables = await db.pool.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        )
        table_names = {t['tablename'] for t in tables}

        required_tables = {
            'catalog_products', 'catalog_watches', 'catalog_product_alerts',
            'catalog_product_identifiers', 'catalog_rules', 'price_snapshots',
            'stock_state', 'app_users', 'tracking_requests',
            'deals', 'config_settings'
        }

        missing = required_tables - table_names
        if not missing:
            check_pass(f"All {len(required_tables)} required tables exist")
        else:
            check_fail(f"Missing tables: {', '.join(sorted(missing))}")
            check_warn("Run: python scripts/init_db.py")

        # Count deals
        deal_count = await db.pool.fetchval('SELECT COUNT(*) FROM deals')
        check_pass(f"deals table has {deal_count} rows")

        # Check config_settings has data
        settings_count = await db.pool.fetchval('SELECT COUNT(*) FROM config_settings')
        if settings_count > 0:
            check_pass(f"config_settings table has {settings_count} entries")
        else:
            check_warn("config_settings table is empty (will be populated on first run)")

        await db.close()

    except Exception as e:
        check_fail(f"Database error: {e}")
        import traceback
        traceback.print_exc()
        return

    section("API Server")

    # 7. Test FastAPI app creation
    try:
        from commerce_platform.web.config import load_web_config
        web_cfg = load_web_config(admin_emails=config.admin_emails)
        app = create_app('config.yaml', web_cfg)

        routes = [r for r in app.routes if hasattr(r, 'path')]
        health_routes = len([r for r in routes if '/health' in str(r.path)])
        deals_routes = len([r for r in routes if '/deals' in str(r.path)])
        api_routes = len([r for r in routes if '/api' in str(r.path)])

        check_pass(f"FastAPI app created with {len(routes)} routes")
        print(f"    - Health: {health_routes} endpoints")
        print(f"    - Deals: {deals_routes} endpoints")
        print(f"    - API: {api_routes} endpoints")

    except Exception as e:
        check_fail(f"Cannot create FastAPI app: {e}")
        return

    section("Worker Tasks")

    # 8. Check worker tasks can be imported
    try:
        from commerce_platform.stock.runner import StockRunner
        from commerce_platform.stock.deal_discovery_watcher import DealDiscoveryWatcher
        from commerce_platform.deals.scorer import DealScorer
        check_pass("All worker components can be imported")
    except Exception as e:
        check_fail(f"Cannot import worker components: {e}")
        return

    section("Configuration Summary")

    print(f"Platform sources:")
    for src in config.platform_sources:
        print(f"  - {src.type} ({src.poll_seconds}s)")

    print(f"\nChannels configured:")
    for ch in config.channels:
        print(f"  - {ch.id}: {ch.name}")

    print(f"\nAdmin emails:")
    for email in config.admin_emails:
        print(f"  - {email}")

    section("System Status")

    if checks_failed == 0:
        print(f"{GREEN}[SUCCESS] ALL CHECKS PASSED{RESET}")
        print(f"\nSystem is ready to start. Follow the steps in QUICKSTART.md:")
        print(f"\n1. Start everything:    python -m commerce_platform")
        print(f"2. Health check:        curl http://localhost:8000/api/system")
        print(f"\nMonitor at: http://localhost:8000/deals")
        return 0
    else:
        print(f"{RED}[ERROR] {checks_failed} CHECKS FAILED{RESET}")
        print(f"{GREEN}[OK] {checks_passed} CHECKS PASSED{RESET}")
        print(f"\nFix the issues above and try again.")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
