#!/usr/bin/env python3
"""
Script to completely cleanup SQS queue and Qdrant database
"""

import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.queue import SQSService
from app.services.vector_store import QdrantService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def cleanup_sqs():
    """Clean up SQS queue"""
    try:
        logger.info("Starting SQS queue cleanup...")
        
        sqs_service = SQSService()
        
        # Purge all messages from queue
        success = sqs_service.purge_queue()
        
        if success:
            logger.info("SQS queue purged successfully")
        else:
            logger.error("Failed to purge SQS queue")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up SQS: {e}")
        return False


def cleanup_qdrant():
    """Clean up Qdrant database"""
    try:
        logger.info("Starting Qdrant database cleanup...")
        
        qdrant_service = QdrantService()
        
        # Get collection info before cleanup
        info_before = qdrant_service.get_collection_info()
        points_before = info_before.get('points_count', 0)
        logger.info(f"Documents in Qdrant before cleanup: {points_before}")
        
        if points_before == 0:
            logger.info("Qdrant database is already empty")
            return True
        
        # Delete all documents
        success = qdrant_service.delete_all_documents()
        
        if success:
            # Get collection info after cleanup
            info_after = qdrant_service.get_collection_info()
            points_after = info_after.get('points_count', 0)
            logger.info(f"Documents in Qdrant after cleanup: {points_after}")
            logger.info(f"Removed {points_before - points_after} documents from Qdrant")
        else:
            logger.error("Failed to cleanup Qdrant database")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up Qdrant: {e}")
        return False


def main():
    """Main function to cleanup everything"""
    try:
        logger.info("Starting complete cleanup of SQS queue and Qdrant database...")
        
        # Cleanup SQS
        sqs_success = cleanup_sqs()
        
        # Cleanup Qdrant
        qdrant_success = cleanup_qdrant()
        
        if sqs_success and qdrant_success:
            logger.info("Complete cleanup finished successfully!")
        else:
            logger.error("Cleanup failed for some components")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 