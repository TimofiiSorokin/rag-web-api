#!/usr/bin/env python3
"""
Script to cleanup duplicate documents in Qdrant vector database
"""

import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.vector_store import QdrantService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Main function to cleanup duplicates"""
    try:
        logger.info("Starting duplicate cleanup...")
        
        # Initialize Qdrant service
        qdrant_service = QdrantService()
        
        # Get collection info before cleanup
        info_before = qdrant_service.get_collection_info()
        logger.info(f"Documents before cleanup: {info_before.get('points_count', 0)}")
        
        # Cleanup duplicates
        success = qdrant_service.cleanup_duplicates()
        
        if success:
            # Get collection info after cleanup
            info_after = qdrant_service.get_collection_info()
            logger.info(f"Documents after cleanup: {info_after.get('points_count', 0)}")
            
            removed = info_before.get('points_count', 0) - info_after.get('points_count', 0)
            logger.info(f"Removed {removed} duplicate documents")
        else:
            logger.error("Failed to cleanup duplicates")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 