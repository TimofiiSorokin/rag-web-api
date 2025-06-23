import logging
import os
import uuid
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.core.config import settings
from app.services.queue import SQSService
from app.services.storage import S3StorageService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services with settings from config
s3_service = S3StorageService(
    endpoint_url=settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None
)
sqs_service = SQSService(
    endpoint_url=settings.SQS_ENDPOINT_URL if settings.SQS_ENDPOINT_URL else None
)

# Debug logging for S3 configuration
logger.info(f"S3 Endpoint URL: {settings.S3_ENDPOINT_URL}")
logger.info(f"S3 Bucket Name: {settings.S3_BUCKET_NAME}")
logger.info(f"AWS Region: {settings.AWS_REGION}")

# Allowed file types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc"}


def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False

    return True


@router.post("/", status_code=status.HTTP_204_NO_CONTENT)
async def ingest_document(file: UploadFile = File(...)) -> Response:
    """
    Ingest document endpoint

    Accepts a file upload, stores it in S3, and publishes ingestion task to SQS.
    Returns 204 No Content on success.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
            )

        if not validate_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Read file content
        file_content = await file.read()

        # Validate file size (max 10MB)
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 10MB",
            )

        # Generate unique document ID
        document_id = str(uuid.uuid4())

        # Upload file to S3
        s3_key = s3_service.upload_file(
            file_data=file_content,
            filename=file.filename,
        )

        if not s3_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage",
            )

        # Prepare message for SQS
        message_body = {
            "document_id": document_id,
            "filename": file.filename,
            "s3_key": s3_key,
            "content_type": file.content_type,
            "file_size": len(file_content),
            "status": "pending",
        }

        # Send message to SQS
        if not sqs_service.send_message(message_body):
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to queue document for processing. "
                    "Please try again later."
                ),
            )

        logger.info(f"Document ingested successfully: {document_id} - {file.filename}")

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document ingestion",
        )


@router.get("/health")
async def ingest_health_check() -> Dict[str, Any]:
    """Health check for ingest service"""
    try:
        # Check S3 connectivity
        s3_healthy = s3_service.create_bucket_if_not_exists()

        # Check SQS connectivity
        sqs_healthy = sqs_service.create_queue_if_not_exists() is not None

        return {
            "status": (
                "healthy"
                if s3_healthy and sqs_healthy
                else "unhealthy"
            ),
            "service": "Document Ingestion API",
            "components": {
                "s3_storage": "healthy" if s3_healthy else "unhealthy",
                "sqs_queue": "healthy" if sqs_healthy else "unhealthy",
            },
        }
    except Exception as e:
        logger.error(f"Ingest health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Document Ingestion API",
            "error": str(e),
        }
