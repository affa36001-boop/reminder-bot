"""Точка входа: запускает бота и планировщик"""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import settings
from database.db import init_db
from handlers import callbacks, create, leads, list as list_h, settings as settings_h, start
from services.scheduler import setup_scheduler
from utils.logger import setup_logger


async def _run_userbot_safe(bot: Bot) -> None:
    """Запускает userbot так, чтобы его падение не уронило основной бот."""
    from services.userbot import run_userbot
    try:
        await run_userbot(bot)
    except Exception as e:
        logger.error(f"Userbot упал: {e}")


async def main() -> None:
    setup_logger()
    await init_db()
    logger.info("DB ready")

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок важен: сначала FSM-роутер create, потом общие callback'и
    dp.include_router(start.router)
    dp.include_router(create.router)
    dp.include_router(list_h.router)
    dp.include_router(settings_h.router)
    dp.include_router(leads.router)
    dp.include_router(callbacks.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    userbot_task = None
    if settings.userbot_enabled:
        userbot_task = asyncio.create_task(_run_userbot_safe(bot))
        logger.info("Userbot enabled")
    else:
        logger.info("Userbot disabled (нет API_ID / API_HASH / TELETHON_SESSION в .env)")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot polling…")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        if userbot_task is not None:
            userbot_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
