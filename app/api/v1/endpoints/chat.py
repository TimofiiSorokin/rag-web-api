from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import logging
import json
import time

from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize RAG service
rag_service = RAGService()


class ChatRequest(BaseModel):
    """Model for chat query"""
    query: str = Field(
        ..., min_length=1, description="User question about uploaded documents"
    )
    max_results: int = Field(
        default=5, ge=1, le=20, description="Maximum number of relevant documents to retrieve"
    )
    include_sources: bool = Field(
        default=True, description="Include sources information in response"
    )


class ChatResponse(BaseModel):
    """Model for chat response"""
    query: str
    answer: str
    sources: list
    processing_time: float


@router.post("/")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint - ask questions about uploaded documents
    
    Accepts a user query and returns the complete answer based on uploaded documents.
    Uses RAG (Retrieval-Augmented Generation) to find relevant context and generate responses.
    """
    try:
        start_time = time.time()
        
        logger.info(f"Chat request received: {request.query}")
        
        # Get relevant documents
        documents = rag_service.retrieve_relevant_documents(request.query, request.max_results)
        
        # Create context
        context = rag_service.create_context_from_documents(documents)
        
        # Generate complete answer
        answer_parts = []
        for chunk in rag_service.generate_answer_stream(request.query, context):
            answer_parts.append(chunk)
        
        answer = "".join(answer_parts)
        processing_time = time.time() - start_time
        
        # Prepare sources info
        sources = []
        if request.include_sources:
            for doc in documents:
                sources.append({
                    "filename": doc.get('filename', 'Unknown'),
                    "score": round(doc.get('score', 0.0), 3),
                    "content_preview": doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', '')
                })
        
        return ChatResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            processing_time=round(processing_time, 3)
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/health")
async def chat_health_check() -> Dict[str, Any]:
    """Health check for chat service"""
    try:
        # Check if OpenAI API key is configured
        openai_configured = bool(rag_service.openai_client.api_key)
        
        # Check Qdrant connection
        qdrant_healthy = rag_service.qdrant_service.create_collection_if_not_exists()
        
        return {
            "status": "healthy" if openai_configured and qdrant_healthy else "unhealthy",
            "service": "Chat API",
            "components": {
                "openai": "configured" if openai_configured else "not_configured",
                "qdrant": "healthy" if qdrant_healthy else "unhealthy"
            }
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Chat API",
            "error": str(e)
        } 