from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "IntelliKYC"
    environment: str = "development"
    debug: bool = True
    
    # API Keys
    ocr_space_api_key: Optional[str] = None
    ibm_watson_api_key: Optional[str] = None
    ibm_watson_url: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # File Upload
    max_file_size_mb: int = 10
    upload_dir: str = "uploads"
    
    # API Configuration
    api_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
