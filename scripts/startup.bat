@echo off
REM Deal Discovery Platform — Startup (Windows)
REM Two simple terminals: API + Workers

cd /d "%~dp0\.."

echo.
echo ===================================================================
echo   Deal Discovery Platform — Startup
echo ===================================================================
echo.

REM Verify system
python verify_system.py >nul 2>&1
if errorlevel 1 (
    echo ERROR: System verification failed
    echo Run: python verify_system.py
    pause
    exit /b 1
)

echo OK: Starting 2 terminals...
echo.

REM Terminal 1: API Server
echo Starting: API Server (port 8000)...
start "API Server" cmd /k python scripts/api_server.py

REM Wait for API to start
timeout /t 2 /nobreak

REM Terminal 2: Workers
echo Starting: Workers (discovery, curation, parser fixing)...
start "Workers" cmd /k python scripts/workers.py

echo.
echo Terminals started. Open browser:
echo   http://localhost:8000/deals
echo.
echo Deals appear in ~60 seconds.
echo.
pause
