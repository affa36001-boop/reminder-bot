"""Точка входа: запускает бот-напоминалку, планировщик и API-сервер."""
import asyncio
import os

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from api.app import create_app
from config import settings
from database.db import init_db
from handlers import callbacks, create, list as list_h, settings as settings_h, start
from services.scheduler import setup_scheduler
from utils.logger import setup_logger


async def main() -> None:
    setup_logger()
    os.makedirs("/app/data", exist_ok=True)
    await init_db()
    logger.info("DB ready")

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(create.router)
    dp.include_router(list_h.router)
    dp.include_router(settings_h.router)
    dp.include_router(callbacks.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    api_server = uvicorn.Server(
        uvicorn.Config(create_app(), host="0.0.0.0", port=settings.api_port,
                       loop="none", log_level="warning")
    )
    logger.info(f"API server starting on port {settings.api_port}")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot polling…")
        await asyncio.gather(dp.start_polling(bot), api_server.serve())
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
