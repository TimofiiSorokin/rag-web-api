import logging
from typing import Any, Dict, List

import openai

from app.core.config import settings
from app.services.vector_store import QdrantService

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG (Retrieval-Augmented Generation) operations"""

    def __init__(self):
        """Initialize RAG service"""
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
            if hasattr(settings, "OPENAI_BASE_URL")
            else None,
        )

        # Initialize Qdrant service
        self.qdrant_service = QdrantService()

        logger.info("RAGService initialized")

    async def generate_response(
        self, query: str, max_results: int = 5, include_sources: bool = True
    ) -> Dict[str, Any]:
        """Generate response using RAG pipeline"""
        try:
            # Retrieve relevant documents
            documents = self.retrieve_relevant_documents(query, max_results)

            # Create context from documents
            context = self.create_context_from_documents(documents)

            # Generate answer using OpenAI
            answer = await self.generate_answer_with_openai(query, context)

            # Prepare response
            response = {
                "query": query,
                "answer": answer,
                "sources": [],
                "processing_time": 0.0,
            }

            # Add sources if requested
            if include_sources and documents:
                response["sources"] = [
                    {
                        "filename": doc.get("filename", "Unknown"),
                        "score": round(doc.get("score", 0.0), 3),
                        "content_preview": doc.get("content", "")[:200] + "..."
                        if len(doc.get("content", "")) > 200
                        else doc.get("content", ""),
                    }
                    for doc in documents
                ]

            return response

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return {
                "query": query,
                "answer": (
                    "I'm sorry, but I encountered an error while processing your "
                    "request. Please try again later."
                ),
                "sources": [],
                "processing_time": 0.0,
            }

    def retrieve_relevant_documents(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from vector store"""
        try:
            documents = self.qdrant_service.search_documents(
                query=query, limit=max_results
            )
            logger.info(f"Retrieved {len(documents)} relevant documents")
            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

    def create_context_from_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Create context string from documents"""
        try:
            if not documents:
                return ""

            context_parts = []
            for doc in documents:
                content = doc.get("content", "")
                if content:
                    context_parts.append(content)

            context = "\n\n".join(context_parts)
            logger.info(f"Created context from {len(documents)} documents")
            return context

        except Exception as e:
            logger.error(f"Error creating context: {e}")
            return ""

    async def generate_answer_with_openai(self, query: str, context: str) -> str:
        """Generate answer using OpenAI API"""
        try:
            if not context:
                return (
                    "I'm sorry, but I don't have enough context to answer your "
                    "question. Please make sure relevant documents have been "
                    "uploaded and processed."
                )

            # Create prompt with context
            prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Answer:"""

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that answers questions "
                            "based on the provided context. Be concise and accurate."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
            )

            answer = response.choices[0].message.content
            logger.info("Generated answer using OpenAI")
            return answer

        except Exception as e:
            logger.error(f"Error generating answer with OpenAI: {e}")
            return (
                "I'm sorry, but I encountered an error while generating the "
                "answer. Please try again later."
            )
