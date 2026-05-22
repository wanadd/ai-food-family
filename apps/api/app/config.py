from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ПланАм API"
    backend_cors_origins: str = "http://localhost:3000"
    telegram_bot_token: str = ""
    telegram_webapp_url: str = ""
    telegram_menu_button_text: str = "Открыть ПланАм"
    database_url: str = "postgresql://aifood:aifood@postgres:5432/aifood"
    redis_url: str = "redis://redis:6379/0"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
