@echo off
REM Deal Discovery Platform — Auto-Startup (Windows)
REM Opens three terminals for API, Workers, and Monitoring

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
echo OK: System verified. Starting 3 terminals...
echo.

REM Terminal 1: API Server
echo Starting Terminal 1: API Server (Port 8000)...
start "Deal Discovery - API Server" cmd /k "cd /d %cd% && title Deal Discovery API Server && uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for API to start
timeout /t 3 /nobreak

REM Terminal 2: Workers
echo Starting Terminal 2: Workers (Discovery, Curation, Parser Fixing)...
start "Deal Discovery - Workers" cmd /k "cd /d %cd% && title Deal Discovery Workers && python -c ^"import asyncio; from pathlib import Path; from dotenv import load_dotenv; from commerce_platform.platform.config.loader import load; from commerce_platform.platform.store.db import Database; from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers; load_dotenv(Path('.env'), override=True); config = load(Path('config.yaml')); db = Database(config.platform.store); exec('^'async def main(): await db.open(); try: await run_stock_and_deals_workers(config, \"config.yaml\", db=db); finally: await db.close()^'); asyncio.run(main())^""

REM Wait for workers to start
timeout /t 2 /nobreak

REM Terminal 3: Browser and monitoring
echo Starting Terminal 3: Monitoring Dashboard...
start "Deal Discovery - Monitor" cmd /k "cd /d %cd% && title Deal Discovery Monitor && python -c ^"import webbrowser; import time; time.sleep(2); webbrowser.open('http://localhost:8000/deals')^" && cmd /k echo Open http://localhost:8000/deals in your browser (already opening...) && echo. && echo Monitoring URLs: && echo   Health: http://localhost:8000/api/health && echo   System: http://localhost:8000/api/system && echo   Deals: http://localhost:8000/deals && echo. && pause"

echo.
echo ===================================================================
echo   System Started
echo ===================================================================
echo.
echo Three terminals opened:
echo   1. API Server      (Port 8000)
echo   2. Workers         (Discovery, Curation, Parser Fixing)
echo   3. Monitor         (Browser + Status)
echo.
echo First discovery runs in ~60 seconds. Deals will appear on /deals page.
echo.
echo To stop: Close each terminal window (Ctrl+C in each)
echo.
echo For more info, see: QUICKSTART.md
echo.
pause
