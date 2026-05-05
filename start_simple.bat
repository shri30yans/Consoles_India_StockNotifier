@echo off
REM Deal Discovery Platform — Startup (Windows)
REM Two terminals: Backend API + Workers

setlocal enabledelayedexpansion

echo.
echo ===================================================================
echo   Deal Discovery Platform — Starting System
echo ===================================================================
echo.

REM Pre-flight check
echo Verifying system...
python verify_system.py >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: System verification failed. Run: python verify_system.py
    pause
    exit /b 1
)
echo OK: System verified. Starting 2 terminals...
echo.

REM Terminal 1: API Server (serves frontend + API)
echo Starting Terminal 1: API Server (Port 8000)...
start "Deal Discovery - API & Frontend" cmd /k "cd /d %cd% && uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for API to start
timeout /t 3 /nobreak

REM Terminal 2: Workers
echo Starting Terminal 2: Workers (Discovery, Curation, Parser Fixing)...
start "Deal Discovery - Workers" cmd /k "cd /d %cd% && python -c ^"import asyncio; from pathlib import Path; from dotenv import load_dotenv; from commerce_platform.platform.config.loader import load; from commerce_platform.platform.store.db import Database; from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers; load_dotenv(Path('.env'), override=True); config = load(Path('config.yaml')); db = Database(config.platform.store); exec('^'async def main(): await db.open(); try: await run_stock_and_deals_workers(config, \"config.yaml\", db=db); finally: await db.close()^'); asyncio.run(main())^""

echo.
echo ===================================================================
echo   System Started
echo ===================================================================
echo.
echo Two terminals opened:
echo   1. API Server (Port 8000)     - Serves both API and frontend
echo   2. Workers                    - Discovery, Curation, Parser Fixing
echo.
echo Next steps:
echo   1. Open browser:   http://localhost:8000/deals
echo   2. Wait 60 seconds for first deal discovery
echo   3. Deals will appear on the page
echo.
echo To stop: Close each terminal (Ctrl+C or close the window)
echo.
pause
