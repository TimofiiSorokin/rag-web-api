#!/bin/bash

# Document worker startup script
echo "Starting Document Worker..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run ./scripts/run_local.sh first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please edit .env file with your configuration"
fi

# Check if LocalStack is running
if ! curl -s http://localhost:4566 > /dev/null 2>&1; then
    echo "Warning: LocalStack is not running on port 4566"
    echo "To start LocalStack, run: ./scripts/setup_localstack.sh"
fi

# Check if Qdrant is running
if ! curl -s http://localhost:6333 > /dev/null 2>&1; then
    echo "Warning: Qdrant is not running on port 6333"
    echo "To start Qdrant, run: ./scripts/setup_localstack.sh"
fi

# Start the worker
echo "Starting Document Worker..."
echo "Worker will process documents from SQS queue"
echo "Press Ctrl+C to stop"

python -c "
import logging
from app.workers.document_worker import DocumentWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Start worker
worker = DocumentWorker()
worker.run()
" 