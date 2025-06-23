from fastapi import APIRouter

from app.api.v1.endpoints import chat, health, ingest

api_router = APIRouter()

# Include endpoints with /rag prefix
api_router.include_router(health.router, prefix="/rag/health", tags=["health"])
api_router.include_router(ingest.router, prefix="/rag/ingest", tags=["ingest"])
api_router.include_router(chat.router, prefix="/rag/chat", tags=["chat"])
