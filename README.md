# FastAPI RAG Web API

Modern FastAPI application for working with RAG (Retrieval-Augmented Generation) system with Docker support and comprehensive tools for document processing and context-based response generation.

## 📋 Project Description

**FastAPI RAG Web API** is a web service that allows you to:
- Upload documents in various formats (PDF, TXT, MD, DOCX, DOC)
- Store them in S3-compatible storage
- Process documents through SQS queue
- Index content in Qdrant vector database
- Generate responses to user queries using OpenAI GPT models
- Provide detailed information about response sources

### 🎯 Key Features

- **📄 Document Processing**: Support for PDF, TXT, Markdown, Word documents
- **🗄️ Storage**: S3-compatible storage for documents
- **🔄 Asynchronous Processing**: SQS queue for document processing
- **🔍 Vector Search**: Qdrant for semantic search
- **🤖 AI Generation**: OpenAI GPT for response generation
- **📊 Monitoring**: Health checks and detailed diagnostics
- **🐳 Docker**: Full containerization support
- **🔒 Security**: Data validation, file size limits
- **📈 Scalability**: Modular architecture

## 🏗️ Project Architecture

```
rag-web-api/
├── app/                          # Main application code
│   ├── main.py                   # FastAPI entry point
│   ├── core/                     # Configuration and utilities
│   │   └── config.py             # Application settings
│   ├── services/                 # Business logic
│   │   ├── storage.py            # S3 storage service
│   │   ├── queue.py              # SQS queue service
│   │   ├── vector_store.py       # Qdrant vector store
│   │   ├── document_processor.py # Document processing with LlamaIndex
│   │   └── rag_service.py        # RAG service with OpenAI
│   └── api/                      # API endpoints
│       └── v1/                   # API version 1
│           ├── router.py         # Main router
│           └── endpoints/        # Endpoint modules
│               ├── health.py     # Health check endpoints
│               ├── ingest.py     # Document upload endpoints
│               └── chat.py       # Chat endpoints
├── docker/                       # Docker configuration
│   ├── prod/                     # Production configuration
│   │   ├── Dockerfile            # Docker image
│   │   ├── docker-compose.yml    # Docker Compose
│   │   └── nginx.conf            # Nginx configuration
│   └── localstack/               # LocalStack configuration
│       └── docker-compose.yml    # LocalStack setup
├── scripts/                      # Startup scripts
│   ├── run_local.sh             # Local startup
│   ├── run_docker.sh            # Docker startup
│   └── setup_localstack.sh      # LocalStack setup
├── requirements/                 # Python dependencies
│   ├── base.txt                 # Minimal runtime dependencies
│   ├── prod.txt                 # Production dependencies
│   └── dev.txt                  # Development dependencies
├── tests/                       # Tests
│   ├── test_ingest.py           # Tests for ingest endpoints
│   └── test_chat.py             # Tests for chat endpoints
├── env.example                   # Environment variables example
└── README.md                     # Documentation
```

## 🚀 Step-by-Step Project Setup

### Step 1: Environment Preparation

#### 1.1 Clone the repository
```bash
git clone <repository-url>
cd rag-web-api
```

#### 1.2 Create virtual environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# For macOS/Linux:
source .venv/bin/activate
# For Windows:
# .venv\Scripts\activate
```

#### 1.3 Install dependencies
```bash
# For development (recommended):
pip install -r requirements/dev.txt

# For production:
# pip install -r requirements/prod.txt

# For minimal runtime:
# pip install -r requirements/base.txt
```

### Step 2: Environment Variables Setup

#### 2.1 Copy configuration file
```bash
cp env.example .env
```

#### 2.2 Edit environment variables
Edit the `.env` file with your settings:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# AWS/LocalStack Configuration
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_ENDPOINT_URL=http://localhost:4566

# S3 Configuration
S3_BUCKET_NAME=documents
S3_ENDPOINT_URL=http://localhost:4566

# SQS Configuration
SQS_QUEUE_NAME=document-processing
SQS_ENDPOINT_URL=http://localhost:4566

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=documents

# Application Configuration
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

### Step 3: LocalStack Setup (for local development)

#### 3.1 Start LocalStack
```bash
# Make script executable
chmod +x scripts/setup_localstack.sh

# Start LocalStack
./scripts/setup_localstack.sh
```

Or manually:
```bash
cd docker/localstack
docker-compose up -d
```

#### 3.2 Verify LocalStack
```bash
# Check LocalStack status
curl http://localhost:4566/health
```

### Step 4: Application Launch

#### 4.1 Local launch (recommended for development)
```bash
# Make script executable
chmod +x scripts/run_local.sh

# Start application
./scripts/run_local.sh
```

Or manually:
```bash
# Start with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4.2 Docker launch (for production)
```bash
# Make script executable
chmod +x scripts/run_docker.sh

# Start via Docker
./scripts/run_docker.sh
```

Or manually:
```bash
cd docker/prod
docker-compose up -d
```

### Step 5: Verification

#### 5.1 Health Check
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed API v1 health check
curl http://localhost:8000/api/v1/health/detailed

# Ingest service health check
curl http://localhost:8000/api/v1/ingest/health

# Chat service health check
curl http://localhost:8000/api/v1/chat/health
```

#### 5.2 API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Usage

### Document Upload

#### POST /api/v1/rag/ingest
Upload a document for processing:

```bash
curl -X POST "http://localhost:8000/api/v1/rag/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/document.pdf"
```

**Supported formats:**
- PDF (`.pdf`)
- Text (`.txt`)
- Markdown (`.md`)
- Word documents (`.docx`, `.doc`)

**Responses:**
- `204 No Content` — successful upload
- `400 Bad Request` — invalid file type or missing filename
- `413 Request Entity Too Large` — file too large (>10MB)
- `500 Internal Server Error` — storage or queue error

### Chat with Documents

#### POST /api/v1/rag/chat/
Query the RAG system to get responses based on uploaded documents:

```bash
curl -X POST "http://localhost:8000/api/v1/rag/chat/" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is contained in the documents? Please provide a brief overview.",
       "max_results": 5,
       "include_sources": true
     }'
```

**Request parameters:**
- `query` (required) — user question
- `max_results` (optional, default 5) — maximum number of relevant documents (1-20)
- `include_sources` (optional, default true) — include source information

**Response example:**
```json
{
  "query": "What is contained in the documents?",
  "answer": "Based on document analysis, the system contains information about...",
  "sources": [
    {
      "filename": "document.pdf",
      "score": 0.95,
      "content_preview": "This document contains detailed information about..."
    }
  ],
  "processing_time": 1.234
}
```

## 🧪 Testing

### Running Tests
```bash
# All tests
python -m pytest tests/ -v
```

### LocalStack for Local Development
```bash
cd docker/localstack
docker-compose up -d
```

### Container Verification
```bash
# Container status
docker-compose ps

# Application logs
docker-compose logs -f app

# Nginx logs
docker-compose logs -f nginx
```


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request