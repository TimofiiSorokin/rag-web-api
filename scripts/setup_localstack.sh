#!/bin/bash

# Setup LocalStack for local development
echo "Setting up LocalStack for local development..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Create docker-compose file for LocalStack
cat > docker/localstack/docker-compose.yml << EOF
version: '3.8'

services:
  localstack:
    image: localstack/localstack:latest
    container_name: localstack
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,sqs
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
      - DOCKER_HOST=unix:///var/run/docker.sock
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
      - "./data:/tmp/localstack/data"
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - "./qdrant_storage:/qdrant/storage"
    restart: unless-stopped
EOF

# Create directories
mkdir -p docker/localstack/data
mkdir -p qdrant_storage

# Start LocalStack and Qdrant
echo "Starting LocalStack and Qdrant..."
cd docker/localstack
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Create S3 bucket
echo "Creating S3 bucket..."
aws --endpoint-url=http://localhost:4566 s3 mb s3://rag-documents

# Create SQS queue
echo "Creating SQS queue..."
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name document-ingestion-queue

echo "LocalStack setup complete!"
echo "S3 endpoint: http://localhost:4566"
echo "SQS endpoint: http://localhost:4566"
echo "Qdrant endpoint: http://localhost:6333"
echo ""
echo "To stop services: cd docker/localstack && docker-compose down" 