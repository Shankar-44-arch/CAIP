#!/bin/sh
set -e

echo "=== Running CAIP Database Initialization ==="
python scripts/init_db.py

echo "=== Starting FastAPI Application ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
