from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Signalpost AI"
    database_url: str = "sqlite:///./signalpost.db"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "none"
    llm_model: str = ""
    max_total_requests: int = Field(default=100, alias="MAX_TOTAL_REQUESTS")
    request_timeout_seconds: float = 15.0
    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()
