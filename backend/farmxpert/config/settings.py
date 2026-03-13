from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices, field_validator
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    app_name: str = Field(default="FarmXpert API")
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    log_level: str = Field(default="INFO")

    openai_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"))
    openai_model: str = Field(default="gpt-4o-mini", validation_alias=AliasChoices("OPENAI_MODEL", "openai_model"))
    openai_max_output_tokens: int = Field(default=2048)
    openai_temperature: float = Field(default=0.4)
    openai_request_timeout: int = Field(default=30)

    mistral_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("MISTRAL_API_KEY", "mistral_api_key"))
    gemini_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINIAPI", "gemini_api_key"),
    )

    # "openai" or "gemini" — controls which LLM is tried first in core_agent
    primary_llm: str = Field(default="openai", validation_alias=AliasChoices("PRIMARY_LLM", "primary_llm"))

    openweather_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("OPENWEATHER_API_KEY", "openweather_api_key"))
    weatherapi_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("WEATHERAPI_KEY", "weatherapi_key"))
    data_gov_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("DATA_GOV_API_KEY", "data_gov_api_key"))
    data_gov_resource_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("DATA_GOV_RESOURCE_ID", "data_gov_resource_id"))
    serpapi_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("SERPAPI_API_KEY", "serpapi_api_key"))

    blynk_token: Optional[str] = Field(default=None, validation_alias=AliasChoices("BLYNK_TOKEN", "blynk_token"))
    blynk_base_url: Optional[str] = Field(default=None, validation_alias=AliasChoices("BLYNK_BASE_URL", "blynk_base_url"))
    gemini_model: str = Field(default="gemini-2.0-flash")
    gemini_temperature: float = Field(default=0.4)  # Lower for faster, more consistent responses
    gemini_request_timeout: int = Field(default=30)  # Generous timeout for complete responses
    gemini_max_output_tokens: int = Field(default=2048)  # Allow full detailed responses
    gemini_top_p: float = Field(default=0.8)  # Focus on most likely tokens
    gemini_top_k: int = Field(default=40)  # Limit vocabulary for speed

    low_llm_mode: bool = Field(default=False)

    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/farmxpert",
        validation_alias=AliasChoices("DATABASE_URL", "database_url")
    )

    model_config = {
        "env_file": [
            str(Path(__file__).resolve().parents[3] / ".env"),
            str(Path(__file__).resolve().parents[2] / ".env"),
            str(Path(__file__).resolve().parents[1] / ".env"),
            ".env"
        ],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_postgres_url(cls, v: str) -> str:
        if not v:
            return v
        
        # Robust trimming
        v = v.strip().replace('"', '').replace("'", "")
        
        # 1. Normalize protocol for SQLAlchemy 1.4+
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        
        # 2. Port fallback fix (PgBouncer bypass often seen in user code)
        if "6432" in v:
            logger.info("Bypassing PgBouncer port 6432 with 5433 for better stability")
            v = v.replace("6432", "5433")
            
        return v


settings = Settings()  # Singleton settings instance


def get_settings() -> Settings:
    """Get the settings instance"""
    return settings

