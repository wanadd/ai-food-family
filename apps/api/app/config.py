from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Food Family API"
    backend_cors_origins: str = "http://localhost:3000"
    telegram_bot_token: str = ""
    telegram_webapp_url: str = ""
    telegram_menu_button_text: str = "Открыть приложение"
    database_url: str = "postgresql://aifood:aifood@postgres:5432/aifood"
    redis_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
