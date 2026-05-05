#!/bin/bash
# Deal Discovery Platform — Startup (Linux/Mac)
# Two simple terminals: API + Workers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo ""
echo "==================================================================="
echo "  Deal Discovery Platform — Startup"
echo "==================================================================="
echo ""

# Verify system
if ! python3 verify_system.py > /dev/null 2>&1; then
    echo "ERROR: System verification failed"
    echo "Run: python3 verify_system.py"
    exit 1
fi

echo "OK: Starting 2 terminals..."
echo ""

# Detect terminal emulator
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Starting: API Server (port 8000)..."
    open -a Terminal "$SCRIPT_DIR/api_server.sh"

    sleep 2

    echo "Starting: Workers (discovery, curation, parser fixing)..."
    open -a Terminal "$SCRIPT_DIR/workers.sh"
else
    # Linux
    if command -v gnome-terminal &> /dev/null; then
        TERM="gnome-terminal"
    elif command -v konsole &> /dev/null; then
        TERM="konsole"
    else
        TERM="xterm"
    fi

    echo "Starting: API Server (port 8000)..."
    case "$TERM" in
        gnome-terminal) gnome-terminal -- bash "$SCRIPT_DIR/api_server.sh" ;;
        konsole) konsole -e bash "$SCRIPT_DIR/api_server.sh" ;;
        xterm) xterm -e bash "$SCRIPT_DIR/api_server.sh" ;;
    esac

    sleep 2

    echo "Starting: Workers (discovery, curation, parser fixing)..."
    case "$TERM" in
        gnome-terminal) gnome-terminal -- bash "$SCRIPT_DIR/workers.sh" ;;
        konsole) konsole -e bash "$SCRIPT_DIR/workers.sh" ;;
        xterm) xterm -e bash "$SCRIPT_DIR/workers.sh" ;;
    esac
fi

echo ""
echo "Terminals started. Open browser:"
echo "  http://localhost:8000/deals"
echo ""
echo "Deals appear in ~60 seconds."
echo ""
