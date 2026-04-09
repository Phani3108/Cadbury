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

    # Auth — if empty, auth is disabled (dev mode only)
    api_key: str = ""

    # LLM
    openai_api_key: str = ""
    openai_model_cheap: str = "gpt-4o-mini"
    openai_model_heavy: str = "gpt-4o"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/delegates.db"

    # MS Graph
    msgraph_tenant_id: str = ""
    msgraph_client_id: str = ""
    msgraph_client_secret: str = ""
    msgraph_user_email: str = ""

    # Polling
    email_poll_interval_seconds: int = 900

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Company enrichment
    apollo_api_key: str = ""

    # Calendar
    calendar_preblock_threshold: float = 0.80

    # Telegram notifications
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # CORS
    frontend_url: str = "http://localhost:3000"

    # Allowlist — comma-separated emails/identifiers permitted to trigger actions
    allowlist: str = ""


settings = Settings()


def get_settings() -> Settings:
    return settings
