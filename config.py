"""Конфигурация бота: читает переменные окружения из .env"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    default_timezone: str
    log_level: str


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан в .env")
    return Settings(
        bot_token=token,
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./reminders.db"),
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = load_settings()
