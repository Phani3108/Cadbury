from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    secret_key: str = "dev-secret-key-change-in-prod"
    debug: bool = True

    # LLM
    openai_api_key: str = ""
    openai_model_cheap: str = "gpt-4o-mini"
    openai_model_heavy: str = "gpt-4o"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/delegates.db"

    # MS Graph
    msgraph_tenant_id: str = ""
    msgraph_client_id: str = ""
    msgraph_client_secret: str = ""
    msgraph_user_email: str = ""

    # Polling
    email_poll_interval_seconds: int = 900

    # CORS
    frontend_url: str = "http://localhost:3000"


settings = Settings()
