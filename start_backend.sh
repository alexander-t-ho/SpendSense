#!/bin/bash

# Start SpendSense Backend Server
# Load environment variables from .env file if it exists
[ -f .env ] && export $(cat .env | grep -v '^#' | xargs)

source venv/bin/activate 2>/dev/null || { python3 -m venv venv && source venv/bin/activate; }
[ -f "data/spendsense.db" ] || python3 -m ingest.__main__ --num-users 50 2>/dev/null
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload




