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

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings object
settings = Settings()
