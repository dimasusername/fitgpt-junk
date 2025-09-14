#!/bin/bash

# AI Chat Application Backend Startup Script

echo "🚀 Starting AI Chat Application Backend..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and configuration"
fi

# Start the server
echo "🌟 Starting FastAPI server on http://localhost:8000"
python run.py