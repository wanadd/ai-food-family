from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ПланАм API"
    backend_cors_origins: str = "http://localhost:3000"
    telegram_bot_token: str = ""
    telegram_api_base_url: str = "https://api.telegram.org"
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
    # Separate key for the recipe image pipeline (never reuse the app key).
    image_openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "PLANAM_IMAGE_OPENAI_API_KEY", "IMAGE_OPENAI_API_KEY"
        ),
    )
    admin_telegram_ids: str = ""
    admin_pin: str = ""
    admin_panel_enabled: bool = True
    backup_root: str = "backups"
    environment: str = "development"

    # Local audit harness — never active when environment != development.
    planam_audit_mode: bool = Field(
        default=False,
        validation_alias=AliasChoices("PLANAM_AUDIT_MODE", "planam_audit_mode"),
    )
    planam_audit_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PLANAM_AUDIT_SECRET", "planam_audit_secret"),
    )

    # Recipe Engine feature flags — enabled by default after Phase 1 activation.
    # Set individual flags to false via env to disable without redeploying code.
    recipe_engine_v1: bool = False
    recipe_collections: bool = True
    recipe_history: bool = True
    recipe_scenarios: bool = True
    recipe_explainability: bool = True
    family_recipe_preferences: bool = True
    # Stage 2A: catalog/menu/search use only gold V2 recipes by default.
    recipe_gold_v2_only: bool = True

    # Phase 3A: automatic meal consumption reminders (off by default).
    meal_consumption_reminders_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "MEAL_CONSUMPTION_REMINDERS_ENABLED",
            "meal_consumption_reminders_enabled",
        ),
    )
    meal_consumption_reminders_dry_run: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "MEAL_CONSUMPTION_REMINDERS_DRY_RUN",
            "meal_consumption_reminders_dry_run",
        ),
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_development(self) -> bool:
        return self.environment.strip().lower() == "development"

    @property
    def effective_image_openai_api_key(self) -> str:
        """Image pipeline key, falling back to the app key only if unset."""
        return (self.image_openai_api_key or self.openai_api_key or "").strip()

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
