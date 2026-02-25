"""
FarmXpert Configuration Management
Centralized configuration using Pydantic Settings
"""

import os
from typing import List, Optional
from pathlib import Path

from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "FarmXpert"
    app_version: str = "1.0.0"
    debug: bool = Field(default=True, env="DEBUG")
    environment: str = Field(default="development", env="ENV")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    
    # API Keys
    openweather_api_key: Optional[str] = Field(default=None, env="OPENWEATHER_API_KEY")
    weatherapi_key: Optional[str] = Field(default=None, env="WEATHERAPI_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Database & Caching
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # External Services
    sms_api_key: Optional[str] = Field(default=None, env="SMS_API_KEY")
    
    # Image Processing
    max_images_per_check: int = Field(default=3, env="MAX_IMAGES_PER_CHECK")
    min_image_width: int = Field(default=400, env="MIN_IMAGE_WIDTH")
    min_image_height: int = Field(default=400, env="MIN_IMAGE_HEIGHT")
    blur_threshold: int = Field(default=100, env="BLUR_THRESHOLD")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/farmxpert.log", env="LOG_FILE")
    
    # Security
    secret_key: Optional[str] = Field(default=None, env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # API Settings
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8080"], env="CORS_ORIGINS")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Dry Run (for testing)
    dry_run: bool = Field(default=True, env="DRY_RUN")
    
    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings

def get_project_root() -> Path:
    """Get the project root directory"""
    return PROJECT_ROOT

def is_development() -> bool:
    """Check if running in development mode"""
    return settings.environment.lower() == "development"

def is_production() -> bool:
    """Check if running in production mode"""
    return settings.environment.lower() == "production"
