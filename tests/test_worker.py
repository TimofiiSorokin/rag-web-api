import pytest
import json
from unittest.mock import patch, MagicMock
from app.workers.document_worker import DocumentWorker


def test_worker_initialization():
    """Test worker initialization"""
    with patch('app.workers.document_worker.SQSService'), \
         patch('app.workers.document_worker.S3StorageService'), \
         patch('app.workers.document_worker.QdrantService'), \
         patch('app.workers.document_worker.DocumentProcessor'):
        
        worker = DocumentWorker()
        assert worker is not None


def test_process_message_success():
    """Test successful message processing"""
    with patch('app.workers.document_worker.SQSService') as mock_sqs, \
         patch('app.workers.document_worker.S3StorageService') as mock_s3, \
         patch('app.workers.document_worker.QdrantService') as mock_qdrant, \
         patch('app.workers.document_worker.DocumentProcessor') as mock_processor:
        
        # Mock services
        mock_processor_instance = MagicMock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.process_document.return_value = True
        
        worker = DocumentWorker()
        
        # Test message
        message = {
            'Body': json.dumps({
                'document_id': 'test-id',
                'filename': 'test.pdf',
                's3_key': 'uploads/test.pdf'
            })
        }
        
        # Process message
        result = worker.process_message(message)
        
        assert result is True
        mock_processor_instance.process_document.assert_called_once_with(
            'uploads/test.pdf', 'test.pdf'
        )


def test_process_message_failure():
    """Test failed message processing"""
    with patch('app.workers.document_worker.SQSService') as mock_sqs, \
         patch('app.workers.document_worker.S3StorageService') as mock_s3, \
         patch('app.workers.document_worker.QdrantService') as mock_qdrant, \
         patch('app.workers.document_worker.DocumentProcessor') as mock_processor:
        
        # Mock services
        mock_processor_instance = MagicMock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.process_document.return_value = False
        
        worker = DocumentWorker()
        
        # Test message
        message = {
            'Body': json.dumps({
                'document_id': 'test-id',
                'filename': 'test.pdf',
                's3_key': 'uploads/test.pdf'
            })
        }
        
        # Process message
        result = worker.process_message(message)
        
        assert result is False


def test_process_message_invalid_json():
    """Test message processing with invalid JSON"""
    with patch('app.workers.document_worker.SQSService') as mock_sqs, \
         patch('app.workers.document_worker.S3StorageService') as mock_s3, \
         patch('app.workers.document_worker.QdrantService') as mock_qdrant, \
         patch('app.workers.document_worker.DocumentProcessor') as mock_processor:
        
        worker = DocumentWorker()
        
        # Test message with invalid JSON
        message = {
            'Body': 'invalid json'
        }
        
        # Process message
        result = worker.process_message(message)
        
        assert result is False


def test_process_single_message_no_messages():
    """Test processing single message when no messages in queue"""
    with patch('app.workers.document_worker.SQSService') as mock_sqs, \
         patch('app.workers.document_worker.S3StorageService') as mock_s3, \
         patch('app.workers.document_worker.QdrantService') as mock_qdrant, \
         patch('app.workers.document_worker.DocumentProcessor') as mock_processor:
        
        # Mock empty queue
        mock_sqs_instance = MagicMock()
        mock_sqs.return_value = mock_sqs_instance
        mock_sqs_instance.receive_messages.return_value = []
        
        worker = DocumentWorker()
        
        # Process single message
        result = worker.process_single_message()
        
        assert result is False


def test_process_single_message_success():
    """Test successful processing of single message"""
    with patch('app.workers.document_worker.SQSService') as mock_sqs, \
         patch('app.workers.document_worker.S3StorageService') as mock_s3, \
         patch('app.workers.document_worker.QdrantService') as mock_qdrant, \
         patch('app.workers.document_worker.DocumentProcessor') as mock_processor:
        
        # Mock services
        mock_sqs_instance = MagicMock()
        mock_sqs.return_value = mock_sqs_instance
        mock_sqs_instance.receive_messages.return_value = [{
            'Body': json.dumps({
                'document_id': 'test-id',
                'filename': 'test.pdf',
                's3_key': 'uploads/test.pdf'
            }),
            'ReceiptHandle': 'test-receipt'
        }]
        
        mock_processor_instance = MagicMock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.process_document.return_value = True
        
        worker = DocumentWorker()
        
        # Process single message
        result = worker.process_single_message()
        
        assert result is True
        mock_sqs_instance.delete_message.assert_called_once_with('test-receipt') 