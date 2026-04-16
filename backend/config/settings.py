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

    # WhatsApp Business API
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_default_to: str = ""

    # Slack
    slack_bot_token: str = ""
    slack_default_channel: str = ""

    # Twilio SMS
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    sms_default_to: str = ""

    # CORS
    frontend_url: str = "http://localhost:3000"

    # Allowlist — comma-separated emails/identifiers permitted to trigger actions
    allowlist: str = ""

    # Voice — STT via Groq Whisper, TTS via ElevenLabs
    groq_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" by default
    tts_cache_ttl_seconds: int = 86_400
    stt_max_audio_mb: int = 25


settings = Settings()


def get_settings() -> Settings:
    return settings
