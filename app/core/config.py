from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    # Basic settings
    PROJECT_NAME: str = "FastAPI RAG Web API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]
    # Database settings (for future use)
    DATABASE_URL: str = ""
    # Logging settings
    LOG_LEVEL: str = "INFO"
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AWS/S3 settings
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "rag-documents"
    S3_ENDPOINT_URL: str = ""  # For LocalStack
    
    # SQS settings
    SQS_QUEUE_NAME: str = "document-ingestion-queue"
    SQS_ENDPOINT_URL: str = ""  # For LocalStack
    
    # Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "documents"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings object
settings = Settings()
