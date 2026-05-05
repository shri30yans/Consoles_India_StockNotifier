#!/bin/bash
# Start Workers

cd "$(dirname "$0")/.."
python3 scripts/workers.py
