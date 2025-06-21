#!/bin/bash

# Script for local FastAPI RAG Web API startup

echo "🚀 Starting FastAPI RAG Web API locally..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements/dev.txt

# Copy .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📋 Copying env.example to .env..."
    cp env.example .env
    echo "⚠️  Don't forget to configure .env file!"
fi

# Start application
echo "🌟 Starting FastAPI application..."
echo "📖 Documentation will be available at: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 