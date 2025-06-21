# FastAPI RAG Web API

Modern FastAPI application for working with RAG (Retrieval-Augmented Generation) system with Docker support.

## 🚀 Features

- **FastAPI 0.104.1** with Python 3.12
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
│   └── api/                      # API endpoints
│       ├── __init__.py
│       └── v1/                   # API version 1
│           ├── __init__.py
│           ├── router.py         # Main router
│           └── endpoints/        # Endpoint modules
│               ├── __init__.py
│               ├── health.py     # Health check endpoints
│               └── rag.py        # RAG endpoints
├── docker/                       # Docker configuration
│   └── prod/                     # Production configuration
│       ├── Dockerfile            # Docker image
│       ├── docker-compose.yml    # Docker Compose
│       ├── nginx.conf            # Nginx configuration
│       └── .dockerignore         # Docker ignore file
├── scripts/                      # Startup scripts
│   ├── run_local.sh             # Local startup
│   └── run_docker.sh            # Docker startup
├── requirements/                 # Python dependencies
│   ├── base.txt                 # Minimal runtime dependencies
│   ├── prod.txt                 # Production dependencies (includes base)
│   └── dev.txt                  # Development dependencies (includes prod)
├── env.example                   # Environment variables example
└── README.md                     # Documentation
```

## 🛠️ Installation and Setup

### Dependency Management

- `requirements/base.txt` — minimal runtime dependencies (FastAPI, pydantic, etc.)
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

2. **Run the local startup script:**
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
pip install -r requirements/dev.txt

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

## 🧪 Testing

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

## 🚀 Production Deployment

1. **Configure environment variables:**
```bash
cp env.example .env
# Edit .env file
```

2. **Start in production mode:**
```bash
cd docker/prod
docker-compose -f docker-compose.yml up -d
```

3. **Configure SSL (optional):**
- Uncomment HTTPS section in `nginx.conf`
- Add SSL certificates to `ssl/` directory

## 🔮 Future Improvements

- [ ] Integration with vector databases (ChromaDB, Pinecone)
- [ ] Support for various LLM models (OpenAI, Anthropic, local)
- [ ] Authentication and authorization system
- [ ] Caching and performance optimization
- [ ] Metrics and monitoring (Prometheus, Grafana)
- [ ] Tests and CI/CD pipeline
- [ ] API documentation with examples

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is distributed under the MIT license. See `LICENSE` file for details.

## 📞 Support

If you have questions or issues, create an issue in the repository.
