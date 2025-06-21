import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for Qdrant vector database operations"""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        """Initialize Qdrant client"""
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = os.getenv('QDRANT_COLLECTION', 'documents')
        self.vector_size = 384  # For sentence-transformers/all-MiniLM-L6-v2
        
    def create_collection_if_not_exists(self) -> bool:
        """Create Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection {self.collection_name} already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Created collection {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to vector store"""
        try:
            if not self.create_collection_if_not_exists():
                return False
            
            # Prepare points for insertion
            points = []
            for doc in documents:
                point = PointStruct(
                    id=doc.get('id'),
                    vector=doc.get('vector', [0.0] * self.vector_size),  # Placeholder vector
                    payload={
                        'content': doc.get('content'),
                        'metadata': doc.get('metadata', {}),
                        'source': doc.get('source'),
                        'filename': doc.get('filename')
                    }
                )
                points.append(point)
            
            # Insert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def search_documents(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents by vector similarity"""
        try:
            if not self.create_collection_if_not_exists():
                return []
            
            # Search in collection
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            # Convert to list of documents
            documents = []
            for result in search_result:
                doc = {
                    'id': result.id,
                    'score': result.score,
                    'content': result.payload.get('content'),
                    'metadata': result.payload.get('metadata', {}),
                    'source': result.payload.get('source'),
                    'filename': result.payload.get('filename')
                }
                documents.append(doc)
            
            logger.info(f"Found {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': info.name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {} 