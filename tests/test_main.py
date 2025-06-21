import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "FastAPI RAG Web API is running!"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FastAPI RAG Web API"


def test_api_v1_health():
    """Test API v1 health endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "endpoint" in data


def test_api_v1_health_detailed():
    """Test detailed health check endpoint"""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "checks" in data


def test_rag_info():
    """Test RAG info endpoint"""
    response = client.get("/api/v1/rag/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "RAG (Retrieval-Augmented Generation) API"
    assert "endpoints" in data


def test_rag_health():
    """Test RAG health endpoint"""
    response = client.get("/api/v1/rag/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data


def test_rag_test():
    """Test RAG test endpoint"""
    response = client.get("/api/v1/rag/test")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "RAG API is working!"
    assert data["status"] == "ready"


def test_rag_query():
    """Test RAG query endpoint"""
    query_data = {
        "query": "Test query",
        "max_results": 3,
        "context_length": 1000
    }
    response = client.post("/api/v1/rag/query", json=query_data)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Test query"
    assert "answer" in data
    assert "sources" in data
    assert "confidence" in data
    assert "processing_time" in data


def test_rag_query_invalid():
    """Test RAG query endpoint with invalid data"""
    query_data = {
        "query": "",  # Empty query - should fail validation
        "max_results": 0  # Invalid number of results - should fail validation
    }
    response = client.post("/api/v1/rag/query", json=query_data)
    assert response.status_code == 422  # Validation error


def test_docs_available():
    """Test documentation availability"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_available():
    """Test ReDoc documentation availability"""
    response = client.get("/redoc")
    assert response.status_code == 200 