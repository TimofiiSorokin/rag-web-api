import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle"""
    # Startup
    logger.info("Starting up FastAPI RAG Web API...")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI RAG Web API...")


def create_application() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "FastAPI RAG Web API - system for working with RAG "
            "(Retrieval-Augmented Generation)"
        ),
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


app = create_application()


@app.get("/")
async def root() -> dict:
    """Root endpoint for API health check"""
    return {
        "message": "FastAPI RAG Web API is running!",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {"status": "healthy", "service": "FastAPI RAG Web API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
