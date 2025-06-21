#!/bin/bash

# Script for running FastAPI RAG Web API in Docker

echo "🐳 Starting FastAPI RAG Web API in Docker..."

# Go to Docker files directory
cd docker/prod

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build image
echo "🔨 Building Docker image..."
docker-compose build --no-cache

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 10

# Check status
echo "📊 Container status:"
docker-compose ps

echo ""
echo "✅ FastAPI RAG Web API started in Docker!"
echo "📖 Documentation: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo "🌐 API: http://localhost:8000/api/v1"
echo ""
echo "To view logs use: docker-compose logs -f"
echo "To stop use: docker-compose down" 