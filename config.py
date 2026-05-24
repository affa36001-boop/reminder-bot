"""Конфигурация бота: читает переменные окружения из .env"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    # Отдельный бот для учёта лидов — опционально. Если не задан, лиды отключены.
    leads_bot_token: str | None
    database_url: str
    default_timezone: str
    log_level: str
    # Userbot (Telethon) — опционально: если не задано, userbot не запускается
    api_id: int | None
    api_hash: str | None
    telethon_session: str | None

    @property
    def leads_enabled(self) -> bool:
        return bool(self.leads_bot_token)

    @property
    def userbot_enabled(self) -> bool:
        return bool(self.api_id and self.api_hash and self.telethon_session
                    and self.leads_bot_token)


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан в .env")
    api_id_raw = os.getenv("API_ID")
    return Settings(
        bot_token=token,
        leads_bot_token=os.getenv("LEADS_BOT_TOKEN") or None,
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./reminders.db"),
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        api_id=int(api_id_raw) if api_id_raw and api_id_raw.isdigit() else None,
        api_hash=os.getenv("API_HASH") or None,
        telethon_session=os.getenv("TELETHON_SESSION") or None,
    )


settings = load_settings()
