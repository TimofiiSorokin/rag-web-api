from fastapi import APIRouter
from app.api.v1.endpoints import health, rag, ingest

api_router = APIRouter()

# Include endpoints
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
