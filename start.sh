#!/bin/bash
# Deal Discovery Platform — Auto-Startup (Linux/Mac)
# Opens three terminals for API, Workers, and Monitoring

set -e

echo ""
echo "==================================================================="
echo "  Deal Discovery Platform — Starting System"
echo "==================================================================="
echo ""

# Pre-flight check
echo "Verifying system..."
if ! python3 verify_system.py > /dev/null 2>&1; then
    echo ""
    echo "ERROR: System verification failed. Run: python3 verify_system.py"
    exit 1
fi
echo "OK: System verified. Starting 3 terminals..."
echo ""

# Detect OS and terminal
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    TERMINAL="Terminal"
    OPEN_CMD="open"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - try common terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        TERMINAL="gnome-terminal"
    elif command -v konsole &> /dev/null; then
        TERMINAL="konsole"
    elif command -v xterm &> /dev/null; then
        TERMINAL="xterm"
    else
        echo "ERROR: No terminal emulator found. Install gnome-terminal, konsole, or xterm."
        exit 1
    fi
else
    echo "ERROR: Unsupported OS: $OSTYPE"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Terminal 1: API Server
echo "Starting Terminal 1: API Server (Port 8000)..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open -a Terminal "$SCRIPT_DIR/terminal1_api.sh"
else
    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && bash terminal1_api.sh"
            ;;
        konsole)
            konsole -e bash -c "cd '$SCRIPT_DIR' && bash terminal1_api.sh"
            ;;
        xterm)
            xterm -e bash -c "cd '$SCRIPT_DIR' && bash terminal1_api.sh"
            ;;
    esac
fi

sleep 3

# Terminal 2: Workers
echo "Starting Terminal 2: Workers (Discovery, Curation, Parser Fixing)..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open -a Terminal "$SCRIPT_DIR/terminal2_workers.sh"
else
    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && bash terminal2_workers.sh"
            ;;
        konsole)
            konsole -e bash -c "cd '$SCRIPT_DIR' && bash terminal2_workers.sh"
            ;;
        xterm)
            xterm -e bash -c "cd '$SCRIPT_DIR' && bash terminal2_workers.sh"
            ;;
    esac
fi

sleep 2

# Terminal 3: Monitor/Browser
echo "Starting Terminal 3: Monitor & Browser..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open -a Terminal "$SCRIPT_DIR/terminal3_monitor.sh"
else
    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && bash terminal3_monitor.sh"
            ;;
        konsole)
            konsole -e bash -c "cd '$SCRIPT_DIR' && bash terminal3_monitor.sh"
            ;;
        xterm)
            xterm -e bash -c "cd '$SCRIPT_DIR' && bash terminal3_monitor.sh"
            ;;
    esac
fi

echo ""
echo "==================================================================="
echo "  System Started"
echo "==================================================================="
echo ""
echo "Three terminals opened:"
echo "  1. API Server      (Port 8000)"
echo "  2. Workers         (Discovery, Curation, Parser Fixing)"
echo "  3. Monitor         (Browser + Status)"
echo ""
echo "First discovery runs in ~60 seconds. Deals will appear on /deals page."
echo ""
echo "To stop: Close each terminal window (Ctrl+C in each)"
echo ""
echo "For more info, see: QUICKSTART.md"
echo ""
