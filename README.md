# FastAPI RAG Web API

Modern FastAPI application for working with RAG (Retrieval-Augmented Generation) system with Docker support.

## 🚀 Features

- **FastAPI 0.104.1** with Python 3.12
- **Document Ingestion** with S3 storage and SQS queuing
- **Vector Database** integration with Qdrant
- **Docker** support for production
- **Nginx** as reverse proxy
- **Quality architecture** with modular separation
- **Health checks** and monitoring
- **CORS** configuration
- **Logging** and error handling
- **Pydantic** for data validation
- **Ready endpoints** for testing

## 📁 Project Structure

```
rag-web-api/
├── app/                          # Main application code
│   ├── __init__.py
│   ├── main.py                   # Main FastAPI file
│   ├── core/                     # Configuration and utilities
│   │   ├── __init__.py
│   │   └── config.py             # Application settings
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── storage.py            # S3 storage service
│   │   ├── queue.py              # SQS queue service
│   │   └── vector_store.py       # Qdrant vector store service
│   └── api/                      # API endpoints
│       ├── __init__.py
│       └── v1/                   # API version 1
│           ├── __init__.py
│           ├── router.py         # Main router
│           └── endpoints/        # Endpoint modules
│               ├── __init__.py
│               ├── health.py     # Health check endpoints
│               ├── rag.py        # RAG endpoints
│               └── ingest.py     # Document ingestion endpoints
├── docker/                       # Docker configuration
│   ├── prod/                     # Production configuration
│   │   ├── Dockerfile            # Docker image
│   │   ├── docker-compose.yml    # Docker Compose
│   │   ├── nginx.conf            # Nginx configuration
│   │   └── .dockerignore         # Docker ignore file
│   └── localstack/               # LocalStack configuration
│       └── docker-compose.yml    # LocalStack setup
├── scripts/                      # Startup scripts
│   ├── run_local.sh             # Local startup
│   ├── run_docker.sh            # Docker startup
│   └── setup_localstack.sh      # LocalStack setup
├── requirements/                 # Python dependencies
│   ├── base.txt                 # Minimal runtime dependencies
│   ├── prod.txt                 # Production dependencies (includes base)
│   └── dev.txt                  # Development dependencies (includes prod)
├── env.example                   # Environment variables example
└── README.md                     # Documentation
```

## 🛠️ Installation and Setup

### Dependency Management

- `requirements/base.txt` — minimal runtime dependencies (FastAPI, pydantic, boto3, llama-index, qdrant-client, etc.)
- `requirements/prod.txt` — production dependencies (includes base, can add prod-only packages)
- `requirements/dev.txt` — development dependencies (includes prod, adds test/lint/dev tools)

**For production:**
```bash
pip install -r requirements/prod.txt
```
**For development:**
```bash
pip install -r requirements/dev.txt
```
**For minimal runtime (e.g. serverless):**
```bash
pip install -r requirements/base.txt
```

### Local Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd rag-web-api
```

2. **Setup LocalStack (optional, for S3/SQS testing):**
```bash
chmod +x scripts/setup_localstack.sh
./scripts/setup_localstack.sh
```

3. **Run the local startup script:**
```bash
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

Or manually:
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements/base.txt

# Copy .env file
cp env.example .env

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Setup

1. **Run the Docker script:**
```bash
chmod +x scripts/run_docker.sh
./scripts/run_docker.sh
```

Or manually:
```bash
cd docker/prod
docker-compose up -d
```

## 🌐 Available Endpoints

### Main Endpoints
- `GET /` - Root endpoint with API information
- `GET /health` - Health check
- `GET /docs` - Swagger documentation
- `GET /redoc` - ReDoc documentation

### API v1
- `GET /api/v1/health/` - Health check for API v1
- `GET /api/v1/health/detailed` - Detailed health check
- `GET /api/v1/rag/` - RAG API information
- `GET /api/v1/rag/health` - Health check for RAG service
- `GET /api/v1/rag/test` - Test endpoint
- `POST /api/v1/rag/query` - Main RAG endpoint
- `POST /api/v1/ingest/` - Document ingestion endpoint
- `GET /api/v1/ingest/health` - Health check for ingest service

## 📄 Document Ingestion

### Upload Document

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/document.pdf"
```

**Supported file types:**
- PDF (`.pdf`)
- Text (`.txt`)
- Markdown (`.md`)
- Word documents (`.docx`, `.doc`)

**Response:**
- `204 No Content` - Success
- `400 Bad Request` - Invalid file type or missing filename
- `413 Request Entity Too Large` - File too large (>10MB)
- `500 Internal Server Error` - Storage or queue error

### Health Check

```bash
curl http://localhost:8000/api/v1/ingest/health
```

## 🧪 Testing

### Test Document Ingestion

```bash
# Create a test file
echo "This is a test document" > test.txt

# Upload the file
curl -X POST "http://localhost:8000/api/v1/ingest/" \
     -F "file=@test.txt"
```

### Test RAG API Query

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is artificial intelligence?",
       "max_results": 3,
       "context_length": 1000
     }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Run Tests

```bash
pytest tests/
```

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

Main variables:
- `DEBUG` - Debug mode
- `LOG_LEVEL` - Logging level
- `SECRET_KEY` - Secret key
- `ALLOWED_HOSTS` - Allowed hosts for CORS
- `AWS_ACCESS_KEY_ID` - AWS access key (use 'test' for LocalStack)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (use 'test' for LocalStack)
- `S3_ENDPOINT_URL` - S3 endpoint URL (http://localhost:4566 for LocalStack)
- `SQS_ENDPOINT_URL` - SQS endpoint URL (http://localhost:4566 for LocalStack)
- `QDRANT_HOST` - Qdrant host (localhost)
- `QDRANT_PORT` - Qdrant port (6333)

### LocalStack Configuration

For local development with S3/SQS mocking:

```bash
# Start LocalStack
./scripts/setup_localstack.sh

# Configure .env
S3_ENDPOINT_URL=http://localhost:4566
SQS_ENDPOINT_URL=http://localhost:4566
```

### Docker Configuration

- **Port**: 8000 (API), 80 (Nginx)
- **Health check**: Automatic status check
- **Logs**: Stored in `logs/` directory
- **Restart policy**: `unless-stopped`

## 📊 Monitoring

### Docker Logs
```bash
cd docker/prod
docker-compose logs -f rag-api
```

### Container Status
```bash
cd docker/prod
docker-compose ps
```

### LocalStack Status
```bash
cd docker/localstack
docker-compose ps
```

## 🚀 Production Deployment

1. **Configure environment variables:**
```bash
cp env.example .env
# Edit .env file with production values
```

2. **Start in production mode:**
```bash
cd docker/prod
docker-compose up -d
```

## 🔄 Workflow

1. **Document Ingestion:**
   - Upload file via `/api/v1/ingest/`
   - File stored in S3
   - Task queued in SQS
   - Worker processes document (to be implemented)
   - Document indexed in Qdrant

2. **RAG Query:**
   - Query sent to `/api/v1/rag/query`
   - Query embedded and searched in Qdrant
   - Relevant documents retrieved
   - Response generated with context

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 📞 Support

If you have questions or issues, create an issue in the repository.
