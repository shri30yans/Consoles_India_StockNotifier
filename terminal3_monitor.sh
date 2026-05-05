#!/bin/bash
# Terminal 3: Monitor & Health Checks

echo ""
echo "==================================================================="
echo "  Deal Discovery — Monitor (Terminal 3)"
echo "==================================================================="
echo ""
echo "Dashboard URLs:"
echo "  • Deals (Live Grid):     http://localhost:8000/deals"
echo "  • Health Check:          http://localhost:8000/api/health"
echo "  • System Status:         http://localhost:8000/api/system"
echo ""
echo "Expected behavior:"
echo "  • Deals page loads with empty grid"
echo "  • First discovery runs in ~60 seconds"
echo "  • Deals appear on grid as they're found"
echo "  • Auto-refreshes every 90 seconds"
echo ""
echo "Opening browser to http://localhost:8000/deals..."
echo ""

cd "$(dirname "$0")"

# Open browser (works on Linux and macOS)
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8000/deals" 2>/dev/null &
elif command -v open &> /dev/null; then
    open "http://localhost:8000/deals" 2>/dev/null &
fi

# Monitor health status
echo "Monitoring health status..."
echo ""

while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Checking system health..."

    if response=$(curl -s http://localhost:8000/api/health 2>/dev/null); then
        echo "  ✓ API is responding"

        if system=$(curl -s http://localhost:8000/api/system 2>/dev/null); then
            overall=$(echo "$system" | grep -o '"overall_status":"[^"]*"' | cut -d'"' -f4)
            active_deals=$(echo "$system" | grep -o '"active_deals":[0-9]*' | cut -d':' -f2)
            pending=$(echo "$system" | grep -o '"pending_approval":[0-9]*' | cut -d':' -f2)

            echo "  Overall Status: $overall"
            echo "  Active Deals: ${active_deals:-0}"
            echo "  Pending Approval: ${pending:-0}"
        fi
    else
        echo "  ✗ API not responding (still starting up...)"
    fi

    echo ""
    sleep 30
done
