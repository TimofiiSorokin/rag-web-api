import logging
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3StorageService:
    """Service for S3 storage operations"""

    def __init__(self, endpoint_url: Optional[str] = None):
        """Initialize S3 client"""
        # Use provided endpoint_url or fall back to settings
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT_URL

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME

        logger.info(f"S3StorageService initialized with endpoint: {self.endpoint_url}")
        logger.info(f"S3StorageService bucket: {self.bucket_name}")

    def create_bucket_if_not_exists(self) -> bool:
        """Create S3 bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                    return True

                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    return False
            else:
                logger.error(f"Error checking bucket: {e}")
                return False

    def upload_file(self, file_data: bytes, filename: str) -> Optional[str]:
        """Upload file to S3"""
        try:
            # Ensure bucket exists
            if not self.create_bucket_if_not_exists():
                return None

            # Generate S3 key with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"uploads/{timestamp}_{filename}"

            # Upload file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=self._get_content_type(
                    filename
                ),
            )

            logger.info(f"File uploaded successfully: {s3_key}")
            return s3_key

        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return None

    def download_file(self, s3_key: str) -> Optional[bytes]:
        """Download file from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            file_data = response["Body"].read()
            logger.info(f"File downloaded successfully: {s3_key}")
            return file_data

        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"File deleted successfully: {s3_key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        extension = filename.lower().split(".")[-1]
        content_types = {
            "pdf": "application/pdf",
            "txt": "text/plain",
            "md": "text/markdown",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword",
        }
        return content_types.get(extension, "application/octet-stream")

    def get_file_url(self, s3_key: str) -> Optional[str]:
        """Generate presigned URL for file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=3600,  # 1 hour
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
