"""Точка входа: запускает бот-напоминалку и планировщик."""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import settings
from database.db import init_db
from handlers import callbacks, create, list as list_h, settings as settings_h, start
from services.scheduler import setup_scheduler
from utils.logger import setup_logger


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
    dp.include_router(callbacks.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot polling…")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
