import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000

    bot_token: str = ""

    database_url: str = "sqlite+aiosqlite:///./data/bot.db"

    log_level: str = "INFO"
    log_file: str = "logs/bot.log"

    bot_name: str = "AI Dialogue Bot"
    max_history_messages: int = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.database_url.startswith("sqlite+aiosqlite:///"):
            db_path = self.database_url.replace("sqlite+aiosqlite:///", "")
            if not os.path.isabs(db_path):
                db_path = Path.cwd() / db_path
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
config = settings