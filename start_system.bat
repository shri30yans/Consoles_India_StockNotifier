@echo off
REM Deal Discovery Platform — System Startup (Windows)

setlocal enabledelayedexpansion

echo ===================================================================
echo   Deal Discovery Platform — System Startup
echo ===================================================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check imports
echo Checking prerequisites...
python -c "from commerce_platform.web.main import create_app; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Cannot import application modules
    echo Make sure you have run: pip install -e .
    pause
    exit /b 1
)

echo.
echo ===================================================================
echo  STARTUP INSTRUCTIONS
echo ===================================================================
echo.

echo To start the system, open THREE PowerShell terminals and run:
echo.
echo TERMINAL 1 — Web API:
echo   uvicorn commerce_platform.web.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo TERMINAL 2 — Workers:
echo   python -c ^"^
echo   import asyncio; from pathlib import Path; from commerce_platform.platform.config.loader import load; from commerce_platform.platform.store.db import Database; from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers; config = load(Path('config.yaml')); db = Database(config.platform.store); async def main(): await db.open(); await run_stock_and_deals_workers(config, 'config.yaml', db=db); await db.close(); asyncio.run(main())^"
echo.
echo TERMINAL 3 — Browser:
echo   start http://localhost:8000/deals
echo.

echo ===================================================================
echo  MONITORING URLS (after startup)
echo ===================================================================
echo.
echo System Status:      http://localhost:8000/health/system
echo Deals Status:       http://localhost:8000/health/deals
echo Recent Deals:       http://localhost:8000/health/deals/recent
echo Pending Approval:   http://localhost:8000/health/deals/pending-approval
echo Public API:         http://localhost:8000/api/deals
echo Deals Frontend:     http://localhost:8000/deals
echo Admin Panel:        http://localhost:8000/admin
echo.

echo ===================================================================
echo  VERIFYING SYSTEM
echo ===================================================================
echo.

echo Checking FastAPI...
python -c "from commerce_platform.web.main import create_app; print('  ^> FastAPI OK')"

echo Checking Workers...
python -c "from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers; print('  ^> Workers OK')"

echo Checking Database...
python -c "^
import asyncio; from commerce_platform.platform.store.db import Database; from commerce_platform.platform.config.loader import load; from pathlib import Path; ^
async def test(): ^
    config = load(Path('config.yaml')); db = Database(config.platform.store); ^
    try: ^
        await db.open(); print('  ^> Database OK'); await db.close() ^
    except Exception as e: print(f'  ^> Database ERROR: {e}') ^
asyncio.run(test())^
"

echo.
echo ===================================================================
echo  READY TO START
echo ===================================================================
echo.
echo Run the three terminal commands above and monitor at:
echo   http://localhost:8000/health/system
echo.
pause
