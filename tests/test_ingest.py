import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def test_ingest_health_check():
    """Test ingest health check endpoint"""
    with patch('app.api.v1.endpoints.ingest.s3_service') as mock_s3, \
         patch('app.api.v1.endpoints.ingest.sqs_service') as mock_sqs:
        
        # Mock successful health checks
        mock_s3.create_bucket_if_not_exists.return_value = True
        mock_sqs.create_queue_if_not_exists.return_value = "http://localhost:4566/queue"
        
        response = client.get("/api/v1/ingest/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Document Ingestion API"
        assert "components" in data


def test_ingest_document_success():
    """Test successful document ingestion"""
    with patch('app.api.v1.endpoints.ingest.s3_service') as mock_s3, \
         patch('app.api.v1.endpoints.ingest.sqs_service') as mock_sqs:
        
        # Mock successful upload and queue
        mock_s3.upload_file.return_value = "uploads/20240101_120000_test.pdf"
        mock_sqs.send_message.return_value = True
        
        # Create test file
        test_file_content = b"Test PDF content"
        
        response = client.post(
            "/api/v1/ingest/",
            files={"file": ("test.pdf", test_file_content, "application/pdf")}
        )
        
        assert response.status_code == 204
        mock_s3.upload_file.assert_called_once()
        mock_sqs.send_message.assert_called_once()


def test_ingest_document_invalid_file_type():
    """Test document ingestion with invalid file type"""
    test_file_content = b"Test content"
    
    response = client.post(
        "/api/v1/ingest/",
        files={"file": ("test.exe", test_file_content, "application/octet-stream")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid file type" in data["detail"]


def test_ingest_document_no_filename():
    """Test document ingestion without filename"""
    test_file_content = b"Test content"
    
    response = client.post(
        "/api/v1/ingest/",
        files={"file": ("", test_file_content, "application/pdf")}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_ingest_document_file_too_large():
    """Test document ingestion with file too large"""
    # Create a large file content (11MB)
    large_content = b"x" * (11 * 1024 * 1024)
    
    response = client.post(
        "/api/v1/ingest/",
        files={"file": ("large.pdf", large_content, "application/pdf")}
    )
    
    assert response.status_code == 413
    data = response.json()
    assert "File too large" in data["detail"]


def test_ingest_document_s3_failure():
    """Test document ingestion when S3 upload fails"""
    with patch('app.api.v1.endpoints.ingest.s3_service') as mock_s3:
        # Mock S3 upload failure
        mock_s3.upload_file.return_value = None
        
        test_file_content = b"Test PDF content"
        
        response = client.post(
            "/api/v1/ingest/",
            files={"file": ("test.pdf", test_file_content, "application/pdf")}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to upload file to storage" in data["detail"]


def test_ingest_document_sqs_failure():
    """Test document ingestion when SQS message fails"""
    with patch('app.api.v1.endpoints.ingest.s3_service') as mock_s3, \
         patch('app.api.v1.endpoints.ingest.sqs_service') as mock_sqs:
        
        # Mock successful S3 upload but failed SQS
        mock_s3.upload_file.return_value = "uploads/20240101_120000_test.pdf"
        mock_sqs.send_message.return_value = False
        
        test_file_content = b"Test PDF content"
        
        response = client.post(
            "/api/v1/ingest/",
            files={"file": ("test.pdf", test_file_content, "application/pdf")}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to queue document for processing" in data["detail"]


def test_ingest_supported_file_types():
    """Test that all supported file types are accepted"""
    supported_files = [
        ("test.pdf", b"PDF content", "application/pdf"),
        ("test.txt", b"Text content", "text/plain"),
        ("test.md", b"Markdown content", "text/markdown"),
        ("test.docx", b"Word content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("test.doc", b"Word content", "application/msword")
    ]
    
    with patch('app.api.v1.endpoints.ingest.s3_service') as mock_s3, \
         patch('app.api.v1.endpoints.ingest.sqs_service') as mock_sqs:
        
        mock_s3.upload_file.return_value = "uploads/test_file"
        mock_sqs.send_message.return_value = True
        
        for filename, content, content_type in supported_files:
            response = client.post(
                "/api/v1/ingest/",
                files={"file": (filename, content, content_type)}
            )
            assert response.status_code == 204, f"Failed for {filename}" 