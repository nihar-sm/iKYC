try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from typing import Optional


class AIServicesConfig(BaseSettings):
    # Groq Configuration
    groq_api_key: Optional[str] = None
    groq_text_model: str = "llama-3.3-70b-versatile"
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Fraud Detection Thresholds
    fraud_threshold_high: float = 0.8
    fraud_threshold_medium: float = 0.5
    fraud_threshold_low: float = 0.3

    # AI Service Settings
    ai_timeout_seconds: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


ai_config = AIServicesConfig()
