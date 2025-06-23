import logging
from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for Qdrant vector database operations"""

    def __init__(self, host: str = None, port: int = None):
        """Initialize Qdrant client"""
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.collection_name = settings.QDRANT_COLLECTION

        self.client = QdrantClient(host=self.host, port=self.port)

        logger.info(f"QdrantService initialized: {self.host}:{self.port}")
        logger.info(f"Collection: {self.collection_name}")

    def create_collection_if_not_exists(self) -> bool:
        """Create collection if it doesn't exist"""
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
                    size=384,  # Dimension for sentence-transformers/all-MiniLM-L6-v2
                    distance=Distance.COSINE,
                ),
            )

            logger.info(f"Created collection: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False

    def document_exists(self, s3_key: str) -> bool:
        """Check if document already exists in collection"""
        try:
            # Search for documents with the same s3_key
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "s3_key",
                            "match": {"value": s3_key}
                        }
                    ]
                },
                limit=1
            )
            return len(results[0]) > 0
        except Exception as e:
            logger.error(f"Failed to check document existence: {e}")
            return False

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to vector store"""
        try:
            if not self.create_collection_if_not_exists():
                return False

            # Check if documents already exist (use first document's s3_key)
            if documents and self.document_exists(documents[0]["s3_key"]):
                logger.warning(f"Document with s3_key {documents[0]['s3_key']} already exists, skipping")
                return True

            # Prepare points for Qdrant
            points = []
            for doc in documents:
                point = PointStruct(
                    id=doc["id"],
                    vector=doc["vector"],
                    payload={
                        "content": doc["content"],
                        "filename": doc.get("filename", "Unknown"),
                        "s3_key": doc.get("s3_key", ""),
                        "chunk_id": doc.get("chunk_id", 0),
                        "chunk_size": doc.get("chunk_size", 0),
                    },
                )
                points.append(point)

            # Add points to collection
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(f"Added {len(points)} documents to collection")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents by query using vector similarity"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Searching documents for query: {query}")
            
            # Load the same model used for document processing
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # Generate embedding for the query
            query_embedding = model.encode(query).tolist()
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Convert results to list of documents
            documents = []
            for result in search_results:
                doc = {
                    "id": result.id,
                    "content": result.payload.get("content", ""),
                    "filename": result.payload.get("filename", "Unknown"),
                    "s3_key": result.payload.get("s3_key", ""),
                    "chunk_id": result.payload.get("chunk_id", 0),
                    "score": result.score,
                }
                documents.append(doc)
            
            logger.info(f"Found {len(documents)} relevant documents")
            return documents

        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []

    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from vector store"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=document_ids,
            )

            logger.info(f"Deleted {len(document_ids)} documents")
            return True

        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    def delete_documents_by_s3_key(self, s3_key: str) -> bool:
        """Delete all documents with specific s3_key"""
        try:
            # Find all documents with the given s3_key
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "s3_key",
                            "match": {"value": s3_key}
                        }
                    ]
                },
                limit=1000  # Adjust as needed
            )
            
            if not results[0]:
                logger.info(f"No documents found with s3_key: {s3_key}")
                return True
            
            # Extract point IDs
            point_ids = [point.id for point in results[0]]
            
            # Delete documents
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids,
            )
            
            logger.info(f"Deleted {len(point_ids)} documents with s3_key: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents by s3_key: {e}")
            return False

    def cleanup_duplicates(self) -> bool:
        """Clean up duplicate documents keeping only the latest version"""
        try:
            # Get all documents
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000  # Adjust as needed
            )
            
            if not results[0]:
                logger.info("No documents to clean up")
                return True
            
            # Group by s3_key
            documents_by_s3_key = {}
            for point in results[0]:
                s3_key = point.payload.get("s3_key", "")
                if s3_key not in documents_by_s3_key:
                    documents_by_s3_key[s3_key] = []
                documents_by_s3_key[s3_key].append(point)
            
            # Find duplicates and keep only the latest (assuming newer documents have higher chunk_id)
            duplicates_found = 0
            for s3_key, points in documents_by_s3_key.items():
                if len(points) > 1:
                    # Sort by chunk_id to keep the latest version
                    points.sort(key=lambda p: p.payload.get("chunk_id", 0))
                    
                    # Keep only the last point (highest chunk_id)
                    points_to_delete = points[:-1]
                    point_ids_to_delete = [p.id for p in points_to_delete]
                    
                    # Delete duplicates
                    self.client.delete(
                        collection_name=self.collection_name,
                        points_selector=point_ids_to_delete,
                    )
                    
                    duplicates_found += len(points_to_delete)
                    logger.info(f"Cleaned up {len(points_to_delete)} duplicates for s3_key: {s3_key}")
            
            if duplicates_found > 0:
                logger.info(f"Total duplicates cleaned up: {duplicates_found}")
            else:
                logger.info("No duplicates found")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup duplicates: {e}")
            return False

    def delete_all_documents(self) -> bool:
        """Delete all documents from the collection"""
        try:
            # Get all documents with higher limit
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=50000  # Increased limit to get all documents
            )
            
            if not results[0]:
                logger.info("Collection is already empty")
                return True
            
            # Extract all point IDs
            point_ids = [point.id for point in results[0]]
            
            logger.info(f"Deleting {len(point_ids)} documents from collection")
            
            # Delete all documents
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids,
            )
            
            logger.info(f"Successfully deleted {len(point_ids)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete all documents: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
