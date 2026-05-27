from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ПланАм API"
    backend_cors_origins: str = "http://localhost:3000"
    telegram_bot_token: str = ""
    telegram_webapp_url: str = ""
    telegram_webhook_url: str = ""
    telegram_menu_button_text: str = "Открыть ПланАм"
    telegram_auto_setup_webhook: bool = True
    telegram_bot_username: str = "am_nam_nam_bot"
    telegram_webhook_secret: str = ""
    database_url: str = "postgresql://aifood:aifood@postgres:5432/aifood"
    redis_url: str = "redis://redis:6379/0"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    admin_telegram_ids: str = ""
    admin_pin: str = ""
    admin_panel_enabled: bool = True
    backup_root: str = "backups"
    environment: str = "development"

    # Recipe Engine feature flags (off by default).
    # These flags gate new domain wiring without changing existing API
    # contracts or database schema in an uncontrolled way.
    recipe_engine_v1: bool = False
    recipe_collections: bool = False
    recipe_history: bool = False
    recipe_scenarios: bool = False
    recipe_explainability: bool = False
    family_recipe_preferences: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_development(self) -> bool:
        return self.environment.strip().lower() == "development"

    def admin_telegram_id_set(self) -> set[int]:
        ids: set[int] = set()
        for part in self.admin_telegram_ids.split(","):
            part = part.strip()
            if part.isdigit():
                ids.add(int(part))
        return ids

    @property
    def admin_panel_enabled_flag(self) -> bool:
        return bool(self.admin_panel_enabled)


settings = Settings()
