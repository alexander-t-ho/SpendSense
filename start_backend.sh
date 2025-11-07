#!/bin/bash

# Start SpendSense Backend Server
# This script starts the FastAPI backend server

echo "🚀 Starting SpendSense Backend Server..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if database exists
if [ ! -f "data/spendsense.db" ]; then
    echo "⚠️  Database not found. Generating synthetic data..."
    python3 -m ingest.__main__ --num-users 50
fi

# Start the backend server
echo ""
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload




