"""Application configuration via Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──
    database_url: str = "postgresql+asyncpg://competity:competity@localhost:5432/competity"

    # ── DeepSeek AI ──
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com"

    # ── Telegram ──
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # ── GitHub ──
    github_token: str = ""

    # ── Reddit ──
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "competity-bot/0.1"

    # ── Product Hunt ──
    producthunt_token: str = ""

    # ── App ──
    app_env: str = "development"
    log_level: str = "INFO"

    # ── Scheduler ──
    collect_cron_hour: int = 3
    collect_cron_minute: int = 0
    report_cron_day_of_week: str = "mon"
    report_cron_hour: int = 9
    report_cron_minute: int = 0

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
