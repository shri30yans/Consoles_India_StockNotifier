#!/bin/bash
# Start API Server

cd "$(dirname "$0")/.."
python3 scripts/api_server.py
