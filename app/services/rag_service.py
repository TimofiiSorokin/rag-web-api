import logging
import openai
from typing import List, Dict, Any, AsyncGenerator
from app.core.config import settings
from app.services.vector_store import QdrantService
from app.services.document_processor import DocumentProcessor
from app.services.storage import S3StorageService

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG (Retrieval-Augmented Generation) operations"""
    
    def __init__(self):
        """Initialize RAG service"""
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize Qdrant service
        self.qdrant_service = QdrantService(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        
        # Initialize dummy S3 service for document processor
        dummy_s3_service = S3StorageService()
        
        # Initialize document processor for embeddings
        self.document_processor = DocumentProcessor(
            s3_service=dummy_s3_service,
            qdrant_service=self.qdrant_service
        )
        
        logger.info("RAG service initialized")
    
    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for the query"""
        try:
            embedding = self.document_processor.embedding_model.get_text_embedding(query)
            logger.debug(f"Generated query embedding: {len(embedding)} dimensions")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
    
    def retrieve_relevant_documents(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from Qdrant"""
        try:
            # Get query embedding
            query_embedding = self.get_query_embedding(query)
            
            # Search in Qdrant
            documents = self.qdrant_service.search_documents(
                query_vector=query_embedding,
                limit=max_results
            )
            
            logger.info(f"Retrieved {len(documents)} relevant documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []
    
    def create_context_from_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Create context string from retrieved documents"""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            filename = doc.get('filename', 'Unknown')
            content = doc.get('content', '')
            score = doc.get('score', 0.0)
            
            context_parts.append(
                f"Document {i} (Source: {filename}, Relevance: {score:.3f}):\n{content}\n"
            )
        
        return "\n".join(context_parts)
    
    def generate_answer_stream(self, query: str, context: str):
        """Generate streaming answer using OpenAI"""
        try:
            # Prepare system message
            system_message = (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Use only the information from the context to answer the question. "
                "If the context doesn't contain enough information to answer the question, "
                "say so clearly. Be concise and accurate in your responses."
            )
            
            # Prepare user message with context
            user_message = f"Context:\n{context}\n\nQuestion: {query}"
            
            # Create streaming response
            stream = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                stream=True
            )
            
            # Stream the response
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Failed to generate streaming answer: {e}")
            yield f"Error generating answer: {str(e)}"
    
    def process_chat_query(self, query: str, max_results: int = 5):
        """Process chat query with RAG pipeline"""
        try:
            logger.info(f"Processing chat query: {query}")
            
            # Step 1: Retrieve relevant documents
            documents = self.retrieve_relevant_documents(query, max_results)
            
            # Step 2: Create context
            context = self.create_context_from_documents(documents)
            
            # Step 3: Generate streaming answer
            for chunk in self.generate_answer_stream(query, context):
                yield chunk
                
        except Exception as e:
            logger.error(f"Failed to process chat query: {e}")
            yield f"Error processing query: {str(e)}" 