from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for API v1"""
    try:
        return {
            "status": "healthy",
            "service": "FastAPI RAG Web API",
            "version": "1.0.0",
            "endpoint": "v1/health"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with additional information"""
    try:
        # Here you can add database checks, external services, etc.
        health_status = {
            "status": "healthy",
            "service": "FastAPI RAG Web API",
            "version": "1.0.0",
            "endpoint": "v1/health/detailed",
            "checks": {
                "api": "healthy",
                "database": "not_configured",  # Will be configured later
            }
        }
        logger.info(
            "Detailed health check completed successfully"
        )
        return health_status
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=500, detail="Detailed health check failed"
        )
