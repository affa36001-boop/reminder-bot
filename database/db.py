"""Инициализация БД и хелперы для работы с напоминаниями"""
from datetime import datetime, timedelta
from typing import Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from database.models import Base, User, Reminder

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Создаёт таблицы при первом запуске"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_user(tg_id: int, username: str | None) -> User:
    async with SessionLocal() as s:
        user = (await s.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
        if user is None:
            user = User(telegram_id=tg_id, username=username, timezone=settings.default_timezone)
            s.add(user)
            await s.commit()
            await s.refresh(user)
        elif user.username != username:
            user.username = username
            await s.commit()
        return user


async def set_user_timezone(tg_id: int, tz: str) -> None:
    async with SessionLocal() as s:
        await s.execute(update(User).where(User.telegram_id == tg_id).values(timezone=tz))
        await s.commit()


async def add_reminder(user_id: int, text: str, remind_at_utc: datetime,
                       recurrence: str = "none", tag: str | None = None,
                       pre_notify_minutes: int = 0) -> Reminder:
    async with SessionLocal() as s:
        r = Reminder(user_id=user_id, text=text, remind_at=remind_at_utc,
                     recurrence=recurrence, tag=tag, pre_notify_minutes=pre_notify_minutes)
        s.add(r)
        await s.commit()
        await s.refresh(r)
        return r


async def get_reminder(reminder_id: int) -> Reminder | None:
    async with SessionLocal() as s:
        return (await s.execute(select(Reminder).where(Reminder.id == reminder_id))).scalar_one_or_none()


async def list_active(user_id: int, from_utc: datetime | None = None,
                      to_utc: datetime | None = None, tag: str | None = None) -> Sequence[Reminder]:
    async with SessionLocal() as s:
        q = select(Reminder).where(Reminder.user_id == user_id, Reminder.status == "active")
        if from_utc:
            q = q.where(Reminder.remind_at >= from_utc)
        if to_utc:
            q = q.where(Reminder.remind_at <= to_utc)
        if tag:
            q = q.where(Reminder.tag == tag)
        q = q.order_by(Reminder.remind_at.asc())
        return (await s.execute(q)).scalars().all()


async def list_due(now_utc: datetime) -> Sequence[Reminder]:
    """Активные напоминания, у которых время уже наступило"""
    async with SessionLocal() as s:
        q = select(Reminder).where(Reminder.status == "active", Reminder.remind_at <= now_utc)
        return (await s.execute(q)).scalars().all()


async def list_pre_due(now_utc: datetime) -> Sequence[Reminder]:
    """Активные напоминания, для которых пора прислать предварительное уведомление"""
    async with SessionLocal() as s:
        q = select(Reminder).where(
            Reminder.status == "active",
            Reminder.pre_notify_minutes > 0,
            Reminder.pre_notified == False,  # noqa: E712
        )
        rows = (await s.execute(q)).scalars().all()
        return [r for r in rows if r.remind_at - timedelta(minutes=r.pre_notify_minutes) <= now_utc < r.remind_at]


async def mark_pre_notified(reminder_id: int) -> None:
    async with SessionLocal() as s:
        await s.execute(update(Reminder).where(Reminder.id == reminder_id).values(pre_notified=True))
        await s.commit()


async def set_status(reminder_id: int, status: str) -> None:
    async with SessionLocal() as s:
        await s.execute(update(Reminder).where(Reminder.id == reminder_id).values(status=status))
        await s.commit()


async def reschedule(reminder_id: int, new_utc: datetime) -> None:
    async with SessionLocal() as s:
        await s.execute(update(Reminder).where(Reminder.id == reminder_id)
                        .values(remind_at=new_utc, pre_notified=False))
        await s.commit()


async def delete_reminder(reminder_id: int) -> None:
    async with SessionLocal() as s:
        await s.execute(delete(Reminder).where(Reminder.id == reminder_id))
        await s.commit()


async def list_tags(user_id: int) -> list[str]:
    async with SessionLocal() as s:
        q = select(Reminder.tag).where(Reminder.user_id == user_id,
                                        Reminder.tag.is_not(None),
                                        Reminder.status == "active").distinct()
        return [t for t in (await s.execute(q)).scalars().all() if t]
