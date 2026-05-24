"""Точка входа: запускает бот-напоминалку, бот учёта лидов и userbot.

Лиды и userbot включаются, только если в .env заданы соответствующие токены/ключи.
Если они пусты, работает только бот-напоминалка.
"""
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


async def _run_userbot_safe(leads_bot: Bot) -> None:
    """Изолирует userbot — его падение не должно валить остальные боты."""
    from services.userbot import run_userbot
    try:
        await run_userbot(leads_bot)
    except Exception as e:
        logger.error(f"Userbot упал: {e}")


async def _polling(bot: Bot, dp: Dispatcher, name: str) -> None:
    """Сбрасывает webhook и стартует long polling для одного бота."""
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info(f"{name}: polling…")
    await dp.start_polling(bot)


def _build_reminder_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    # Порядок важен: сначала FSM-роутер create, потом общие callback'и
    dp.include_router(start.router)
    dp.include_router(create.router)
    dp.include_router(list_h.router)
    dp.include_router(settings_h.router)
    dp.include_router(callbacks.router)
    return bot, dp


def _build_leads_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.leads_bot_token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(leads.router)
    return bot, dp


async def main() -> None:
    setup_logger()
    await init_db()
    logger.info("DB ready")

    reminder_bot, reminder_dp = _build_reminder_bot()
    scheduler = setup_scheduler(reminder_bot)
    scheduler.start()
    logger.info("Scheduler started")

    leads_bot: Bot | None = None
    leads_dp: Dispatcher | None = None
    if settings.leads_enabled:
        leads_bot, leads_dp = _build_leads_bot()
        logger.info("Leads bot enabled")
    else:
        logger.info("Leads bot disabled (LEADS_BOT_TOKEN пуст)")

    userbot_task = None
    if settings.userbot_enabled and leads_bot is not None:
        userbot_task = asyncio.create_task(_run_userbot_safe(leads_bot))
        logger.info("Userbot enabled")
    elif not settings.userbot_enabled:
        logger.info("Userbot disabled (нет API_ID / API_HASH / TELETHON_SESSION)")

    polling_tasks = [asyncio.create_task(_polling(reminder_bot, reminder_dp, "Reminder bot"))]
    if leads_bot is not None and leads_dp is not None:
        polling_tasks.append(asyncio.create_task(_polling(leads_bot, leads_dp, "Leads bot")))

    try:
        await asyncio.gather(*polling_tasks)
    finally:
        scheduler.shutdown(wait=False)
        if userbot_task is not None:
            userbot_task.cancel()
        await reminder_bot.session.close()
        if leads_bot is not None:
            await leads_bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
