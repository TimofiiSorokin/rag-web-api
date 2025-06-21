import json
import logging
import time
import os
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.queue import SQSService
from app.services.storage import S3StorageService
from app.services.vector_store import QdrantService
from app.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class DocumentWorker:
    """Worker for processing documents from SQS queue"""
    
    def __init__(self):
        """Initialize worker with services"""
        # Initialize services with settings from config
        self.sqs_service = SQSService(
            endpoint_url=settings.SQS_ENDPOINT_URL if settings.SQS_ENDPOINT_URL else None
        )
        self.s3_service = S3StorageService(
            endpoint_url=settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None
        )
        self.qdrant_service = QdrantService(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        
        # Initialize document processor
        self.document_processor = DocumentProcessor(
            s3_service=self.s3_service,
            qdrant_service=self.qdrant_service
        )
        
        logger.info("Document worker initialized")
    
    def process_message(self, message: Dict[str, Any]) -> bool:
        """Process a single message from SQS"""
        try:
            # Parse message body
            message_body = json.loads(message['Body'])
            
            document_id = message_body.get('document_id')
            filename = message_body.get('filename')
            s3_key = message_body.get('s3_key')
            
            logger.info(f"Processing document: {document_id} - {filename}")
            
            # Process document
            success = self.document_processor.process_document(s3_key, filename)
            
            if success:
                logger.info(f"Successfully processed document: {document_id}")
                return True
            else:
                logger.error(f"Failed to process document: {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False
    
    def run(self, max_messages: int = 10, poll_interval: int = 5):
        """Run worker loop"""
        logger.info("Starting document worker...")
        
        while True:
            try:
                # Receive messages from SQS
                messages = self.sqs_service.receive_messages(max_messages)
                
                if not messages:
                    logger.debug("No messages received, waiting...")
                    time.sleep(poll_interval)
                    continue
                
                # Process each message
                for message in messages:
                    try:
                        success = self.process_message(message)
                        
                        if success:
                            # Delete message from queue on success
                            self.sqs_service.delete_message(message['ReceiptHandle'])
                            logger.info("Message deleted from queue")
                        else:
                            # Keep message in queue for retry
                            logger.warning("Message processing failed, keeping in queue")
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # Keep message in queue for retry
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(poll_interval)
    
    def process_single_message(self) -> bool:
        """Process a single message (for testing)"""
        messages = self.sqs_service.receive_messages(max_messages=1)
        
        if not messages:
            logger.info("No messages in queue")
            return False
        
        message = messages[0]
        success = self.process_message(message)
        
        if success:
            self.sqs_service.delete_message(message['ReceiptHandle'])
        
        return success


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run worker
    worker = DocumentWorker()
    worker.run() 