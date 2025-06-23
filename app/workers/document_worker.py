import json
import logging
import time
import uuid
from typing import Any, Dict

from app.services.document_processor import DocumentProcessor
from app.services.queue import SQSService
from app.services.storage import S3StorageService
from app.services.vector_store import QdrantService

logger = logging.getLogger(__name__)


class DocumentWorker:
    """Worker for processing documents from SQS queue"""

    def __init__(self):
        """Initialize document worker"""
        self.s3_service = S3StorageService()
        self.sqs_service = SQSService()
        self.document_processor = DocumentProcessor()
        self.qdrant_service = QdrantService()

        logger.info("DocumentWorker initialized")

    def process_message(self, message: Dict[str, Any]) -> bool:
        """Process a single message from SQS"""
        try:
            # Parse message body
            message_body = json.loads(message["Body"])
            s3_key = message_body.get("s3_key")
            filename = message_body.get("filename")

            if not s3_key or not filename:
                logger.error("Invalid message format")
                return False

            logger.info(f"Processing document: {filename} ({s3_key})")

            # Download file from S3
            file_data = self.s3_service.download_file(s3_key)
            if not file_data:
                logger.error(f"Failed to download file: {s3_key}")
                return False

            # Save file temporarily
            temp_file_path = f"/tmp/{filename}"
            with open(temp_file_path, "wb") as f:
                f.write(file_data)

            try:
                # Process document
                result = self.document_processor.process_file(temp_file_path)
                if "error" in result:
                    logger.error(f"Document processing failed: {result['error']}")
                    return False

                # Store in vector database
                documents_for_qdrant = []
                for i, (text, embedding) in enumerate(
                    zip(result["texts"], result["embeddings"])
                ):
                    doc = {
                        "id": str(uuid.uuid4()),
                        "content": text,
                        "vector": embedding,
                        "filename": filename,
                        "s3_key": s3_key,
                        "chunk_id": i,
                        "chunk_size": len(text),
                    }
                    documents_for_qdrant.append(doc)

                success = self.qdrant_service.add_documents(documents_for_qdrant)
                if not success:
                    logger.error("Failed to store documents in vector database")
                    return False

                logger.info(
                    f"Successfully processed document: {filename} "
                    f"({len(documents_for_qdrant)} chunks)"
                )
                return True

            finally:
                # Clean up temporary file
                import os

                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False

    def run(self):
        """Main worker loop"""
        logger.info("Starting document worker...")

        while True:
            try:
                # Receive messages from SQS
                messages = self.sqs_service.receive_messages(max_messages=10)

                if not messages:
                    logger.debug("No messages received, waiting...")
                    time.sleep(5)
                    continue

                # Process each message
                for message in messages:
                    success = self.process_message(message)

                    if success:
                        # Delete message from queue
                        self.sqs_service.delete_message(message["ReceiptHandle"])
                        logger.info("Message processed and deleted from queue")
                    else:
                        logger.error("Message processing failed, keeping in queue")

            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(10)  # Wait before retrying

    def stop(self):
        """Stop the worker"""
        logger.info("Stopping document worker...")
        # Add any cleanup logic here


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run worker
    worker = DocumentWorker()
    worker.run()
