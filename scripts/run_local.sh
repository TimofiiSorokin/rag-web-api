#!/bin/bash

# Local development startup script
echo "Starting FastAPI RAG Web API locally..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements/base.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please edit .env file with your configuration"
fi

# Check if LocalStack is running
if ! curl -s http://localhost:4566 > /dev/null 2>&1; then
    echo "Warning: LocalStack is not running on port 4566"
    echo "To start LocalStack, run: ./scripts/setup_localstack.sh"
    echo "Or set S3_ENDPOINT_URL and SQS_ENDPOINT_URL to empty in .env for local file storage"
fi

# Check if Qdrant is running
if ! curl -s http://localhost:6333 > /dev/null 2>&1; then
    echo "Warning: Qdrant is not running on port 6333"
    echo "To start Qdrant, run: ./scripts/setup_localstack.sh"
fi

# Start the application
echo "Starting FastAPI application..."
echo "API will be available at: http://localhost:8000"
echo "Documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 