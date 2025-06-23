"""
Async tests for POST /api/v1/ingest/ endpoint
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from app.api.v1.endpoints.ingest import ingest_document

pytestmark = pytest.mark.asyncio


def make_mock_file(filename, content_type, content):
    mock_file = MagicMock()
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.read = AsyncMock(return_value=content)
    return mock_file


@pytest.mark.asyncio
async def test_ingest_document_success():
    """Test successful document ingestion"""
    with patch('app.api.v1.endpoints.ingest.s3_service') as mock_s3, \
         patch('app.api.v1.endpoints.ingest.sqs_service') as mock_sqs:
        
        # Mock successful operations
        mock_s3.upload_file.return_value = "uploads/test.pdf"
        mock_sqs.send_message.return_value = True
        
        # Create mock file
        mock_file = make_mock_file("test.pdf", "application/pdf", b"Test PDF content")
        
        # Test function call
        result = await ingest_document(mock_file)
        
        # Verify result
        from starlette.responses import Response
        assert isinstance(result, Response)
        assert result.status_code == 204
        
        # Verify services were called
        mock_s3.upload_file.assert_called_once()
        mock_sqs.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_document_invalid_file_type():
    """Test document ingestion with invalid file type"""
    # Create mock file with invalid type
    mock_file = make_mock_file("test.exe", "application/octet-stream", b"Test content")
    
    # Test function call - should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await ingest_document(mock_file)
    
    assert exc_info.value.status_code == 400
    assert "Invalid file type" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_ingest_document_s3_failure():
    """Test document ingestion when S3 upload fails"""
    with patch('app.api.v1.endpoints.ingest.s3_service') as mock_s3:
        # Mock S3 upload failure
        mock_s3.upload_file.return_value = None
        
        # Create mock file
        mock_file = make_mock_file("test.pdf", "application/pdf", b"Test PDF content")
        
        # Test function call - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await ingest_document(mock_file)
        
        assert exc_info.value.status_code == 500
        assert "Failed to upload file to storage" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_ingest_document_sqs_failure():
    """Test document ingestion when SQS message fails"""
    with patch('app.api.v1.endpoints.ingest.s3_service') as mock_s3, \
         patch('app.api.v1.endpoints.ingest.sqs_service') as mock_sqs:
        
        # Mock successful S3 but failed SQS
        mock_s3.upload_file.return_value = "uploads/test.pdf"
        mock_sqs.send_message.return_value = False
        
        # Create mock file
        mock_file = make_mock_file("test.pdf", "application/pdf", b"Test PDF content")
        
        # Test function call - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await ingest_document(mock_file)
        
        assert exc_info.value.status_code == 500
        assert "Failed to queue document for processing" in str(exc_info.value.detail) 