"""Планировщик: раз в минуту проверяет напоминания и шлёт уведомления.

Зачем интервал, а не cron на каждое напоминание:
- проще (одно задание в APScheduler)
- переживает рестарты — БД хранит remind_at
- обрабатывает «пропущенные» напоминания после простоя
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import (SessionLocal, list_due, list_pre_due, mark_pre_notified,
                         reschedule, set_status)
from database.models import User
from keyboards.inline import reminder_actions
from services.parser import next_occurrence


async def _get_user_by_id(s: AsyncSession, user_id: int) -> User | None:
    return (await s.execute(select(User).where(User.id == user_id))).scalar_one_or_none()


async def _tick(bot: Bot) -> None:
    now_utc = datetime.utcnow()

    # 1) Предварительные уведомления
    pre_due = await list_pre_due(now_utc)
    for r in pre_due:
        async with SessionLocal() as s:
            user = await _get_user_by_id(s, r.user_id)
        if user is None:
            continue
        local = r.remind_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(user.timezone))
        tag = f" #{r.tag}" if r.tag else ""
        try:
            await bot.send_message(
                user.telegram_id,
                f"🔔 <b>Скоро напоминание</b> (через {r.pre_notify_minutes} мин){tag}\n"
                f"⏰ {local.strftime('%d.%m.%Y %H:%M')}\n"
                f"📝 {r.text}",
                reply_markup=reminder_actions(r.id),
            )
            await mark_pre_notified(r.id)
        except Exception as e:
            logger.error(f"pre-notify failed for #{r.id}: {e}")

    # 2) Основные уведомления
    due = await list_due(now_utc)
    for r in due:
        async with SessionLocal() as s:
            user = await _get_user_by_id(s, r.user_id)
        if user is None:
            continue
        local = r.remind_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(user.timezone))
        tag = f" #{r.tag}" if r.tag else ""
        try:
            await bot.send_message(
                user.telegram_id,
                f"⏰ <b>Напоминание!</b>{tag}\n"
                f"🕐 {local.strftime('%d.%m.%Y %H:%M')}\n"
                f"📝 {r.text}",
                reply_markup=reminder_actions(r.id),
            )
        except Exception as e:
            logger.error(f"notify failed for #{r.id}: {e}")
            continue

        # Повтор? — двигаем remind_at. Иначе закрываем как done.
        nxt = next_occurrence(r.remind_at, r.recurrence)
        if nxt is not None:
            await reschedule(r.id, nxt)
        else:
            await set_status(r.id, "done")
        logger.info(f"sent reminder #{r.id} to user {user.telegram_id}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(_tick, "interval", seconds=30, kwargs={"bot": bot},
                      id="reminder_tick", coalesce=True, max_instances=1)
    return scheduler
