"""Просмотр напоминаний: список, сегодня, неделя — все с inline-кнопками управления"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_or_create_user, list_active
from keyboards.inline import list_item_actions
from keyboards.reply import main_menu

router = Router(name="list")


def _fmt(utc_dt: datetime, tz_name: str) -> str:
    return utc_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz_name)).strftime("%d.%m %H:%M")


async def _render(msg: Message, title: str, from_utc: datetime | None, to_utc: datetime | None) -> None:
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    items = await list_active(user.id, from_utc=from_utc, to_utc=to_utc)
    if not items:
        await msg.answer(f"{title}\n\n📭 Пусто.", reply_markup=main_menu())
        return
    await msg.answer(f"{title}  ({len(items)})", reply_markup=main_menu())
    for r in items:
        tag = f" #{r.tag}" if r.tag else ""
        rec = f" 🔁{r.recurrence}" if r.recurrence != "none" else ""
        pre = f" 🔔{r.pre_notify_minutes}м" if r.pre_notify_minutes else ""
        body = (f"⏰ <b>{_fmt(r.remind_at, user.timezone)}</b>{rec}{pre}{tag}\n"
                f"📝 {r.text}\n"
                f"<code>id: {r.id}</code>")
        await msg.answer(body, reply_markup=list_item_actions(r.id))


@router.message(Command("list"))
@router.message(F.text == "📋 Мои напоминания")
async def cmd_list(msg: Message) -> None:
    await _render(msg, "📋 <b>Все активные напоминания</b>", from_utc=datetime.utcnow(), to_utc=None)


@router.message(Command("today"))
@router.message(F.text == "📅 На сегодня")
async def cmd_today(msg: Message) -> None:
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    tz = ZoneInfo(user.timezone)
    now_local = datetime.now(tz)
    start = now_local
    end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
    await _render(
        msg, "📅 <b>На сегодня</b>",
        from_utc=start.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
        to_utc=end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
    )


@router.message(Command("week"))
@router.message(F.text == "📆 На неделю")
async def cmd_week(msg: Message) -> None:
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    tz = ZoneInfo(user.timezone)
    now_local = datetime.now(tz)
    end_local = now_local + timedelta(days=7)
    await _render(
        msg, "📆 <b>На неделю</b>",
        from_utc=now_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
        to_utc=end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
    )
