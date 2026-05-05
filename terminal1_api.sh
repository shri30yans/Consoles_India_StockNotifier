#!/bin/bash
# Terminal 1: API Server

set -e

echo ""
echo "==================================================================="
echo "  Deal Discovery — API Server (Terminal 1)"
echo "==================================================================="
echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo ""
echo "Expected output:"
echo "  INFO:     Uvicorn running on http://0.0.0.0:8000"
echo "  INFO:     Application startup complete"
echo ""
echo "Press Ctrl+C to stop."
echo ""

cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1

uvicorn commerce_platform.web.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload

trap "echo 'API Server stopped'; exit 0" EXIT
