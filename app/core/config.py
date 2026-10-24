"""
Core configuration management for the Financial Risk Analysis and Fraud Detection System.
Uses environment variables with sensible defaults for development.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "mysql+pymysql://fraud_user:password@localhost:3306/fraud_detection_db"
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "fraud_detection_db"
    db_user: str = "fraud_user"
    db_password: str = "password"
    db_pool_size: int = 10
    db_pool_recycle: int = 3600
    
    # FastAPI Configuration
    fastapi_host: str = "127.0.0.1"
    fastapi_port: int = 8000
    debug: bool = True
    environment: str = "development"  # development, staging, production
    
    # JWT & Security
    secret_key: str = "dev_secret_key_change_in_production_minimum_32_chars_required"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    admin_email: str = "admin@fraud-detection.local"
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8501"]
    
    # Streamlit Configuration
    streamlit_server_port: int = 8501
    streamlit_server_address: str = "127.0.0.1"
    api_base_url: str = "http://127.0.0.1:8000"
    
    # ML Configuration
    ml_model_threshold: float = 0.5
    enable_ml_detection: bool = True
    
    # Dataset Configuration
    dataset_path: str = "data/raw/creditcard.csv"
    synthetic_data_size: int = 10000
    
    # Security
    max_upload_size_mb: int = 100
    rate_limit_login_attempts: int = 5
    rate_limit_window_seconds: int = 900  # 15 minutes
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/app.log"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache to ensure we only create the settings object once.
    """
    return Settings()
