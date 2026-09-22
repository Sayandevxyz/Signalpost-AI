from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Signalpost AI"
    database_url: str = "sqlite:///./signalpost.db"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "none"
    llm_model: str = ""
    max_total_requests: int = Field(default=100, alias="MAX_TOTAL_REQUESTS")
    max_response_size_mb: int = Field(default=10, alias="MAX_RESPONSE_SIZE_MB")
    request_timeout_seconds: float = 15.0


settings = Settings()
