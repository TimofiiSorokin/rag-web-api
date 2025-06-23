import logging
import time
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize RAG service
rag_service = RAGService()


class ChatRequest(BaseModel):
    """Model for chat query"""

    query: str = Field(
        ...,
        min_length=1,
        description="User question about uploaded documents",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of relevant documents to retrieve",
    )
    include_sources: bool = Field(
        default=True, description="Include sources information in response"
    )


class ChatResponse(BaseModel):
    """Model for chat response"""

    query: str
    answer: str
    sources: list = Field(default_factory=list)
    processing_time: float


@router.post("/")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Chat endpoint for querying documents"""
    start_time = time.time()

    try:
        # Generate response using RAG service
        response_data = await rag_service.generate_response(
            query=request.query,
            max_results=request.max_results,
            include_sources=request.include_sources,
        )

        processing_time = time.time() - start_time

        return ChatResponse(
            query=response_data["query"],
            answer=response_data["answer"],
            sources=response_data.get("sources", []),
            processing_time=processing_time,
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        processing_time = time.time() - start_time

        # Return default response on error
        return ChatResponse(
            query=request.query,
            answer=(
                "I'm sorry, but the provided context doesn't include a specific "
                "test query to respond to. If you have a question or need "
                "assistance with a particular topic or query related to the "
                "context provided, feel free to ask for help."
            ),
            sources=[],
            processing_time=processing_time,
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
            "status": "healthy"
            if openai_configured and qdrant_healthy
            else "unhealthy",
            "service": "Chat API",
            "components": {
                "openai": "configured" if openai_configured else "not_configured",
                "qdrant": "healthy" if qdrant_healthy else "unhealthy",
            },
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Chat API",
            "error": str(e),
        }
