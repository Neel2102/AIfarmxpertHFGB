from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = Field(default="FarmXpert API")
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    log_level: str = Field(default="INFO")

    openai_api_key: str | None = Field(default=None, validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"))
    mistral_api_key: str | None = Field(default=None, validation_alias=AliasChoices("MISTRAL_API_KEY", "mistral_api_key"))
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINIAPI", "gemini_api_key"),
    )

    openweather_api_key: str | None = Field(default=None, validation_alias=AliasChoices("OPENWEATHER_API_KEY", "openweather_api_key"))
    weatherapi_key: str | None = Field(default=None, validation_alias=AliasChoices("WEATHERAPI_KEY", "weatherapi_key"))
    data_gov_api_key: str | None = Field(default=None, validation_alias=AliasChoices("DATA_GOV_API_KEY", "data_gov_api_key"))
    data_gov_resource_id: str | None = Field(default=None, validation_alias=AliasChoices("DATA_GOV_RESOURCE_ID", "data_gov_resource_id"))
    serpapi_api_key: str | None = Field(default=None, validation_alias=AliasChoices("SERPAPI_API_KEY", "serpapi_api_key"))

    blynk_token: str | None = Field(default=None, validation_alias=AliasChoices("BLYNK_TOKEN", "blynk_token"))
    blynk_base_url: str | None = Field(default=None, validation_alias=AliasChoices("BLYNK_BASE_URL", "blynk_base_url"))
    gemini_model: str = Field(default="gemini-flash-latest")
    gemini_temperature: float = Field(default=0.4)  # Lower for faster, more consistent responses
    gemini_request_timeout: int = Field(default=20)  # Reduced timeout for faster failure detection
    gemini_max_output_tokens: int = Field(default=512)  # Keep outputs concise by default; can be overridden via .env
    gemini_top_p: float = Field(default=0.8)  # Focus on most likely tokens
    gemini_top_k: int = Field(default=40)  # Limit vocabulary for speed

    low_llm_mode: bool = Field(default=False)

    database_url: str = Field(default="sqlite:///./farmxpert.db")
    redis_url: str = Field(default="redis://localhost:6379/0")
    static_data_dir: str = Field(default="data/static")
    
    # Authentication
    secret_key: str = Field(default="your-secret-key-change-in-production")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    model_config = {
        "env_file": str(Path(__file__).resolve().parents[1] / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()  # Singleton settings instance


def get_settings() -> Settings:
    """Get the settings instance"""
    return settings

