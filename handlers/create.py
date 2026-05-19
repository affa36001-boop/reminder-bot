"""Создание напоминания через FSM и inline-кнопки.

Сценарий:
1. Кнопка «➕ Создать» → спрашиваем текст напоминания.
2. Получили текст → если в нём есть дата/время — переходим сразу к повтору; иначе календарь.
3. Календарь → день → час → минута → повтор → предварительное уведомление → тег → сохранение.

Дополнительно: если пользователь сразу пишет «завтра в 15:00 встреча #работа»,
бот распознаёт и предлагает быстрое сохранение.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger

from database.db import add_reminder, get_or_create_user, list_tags
from keyboards.inline import (build_calendar, build_time,
                              build_pre_notify, build_recurrence, build_tags)
from keyboards.reply import main_menu
from services.parser import extract_tag, parse_when

router = Router(name="create")


class Create(StatesGroup):
    waiting_text = State()
    waiting_date = State()
    waiting_time = State()
    waiting_recurrence = State()
    waiting_pre_notify = State()
    waiting_tag = State()


def _fmt_local(utc_dt: datetime, tz_name: str) -> str:
    return utc_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz_name)).strftime("%d.%m.%Y %H:%M")


# ────── вход в сценарий ──────

@router.message(Command("new"))
@router.message(F.text == "➕ Создать")
async def start_create(msg: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Create.waiting_text)
    await msg.answer(
        "📝 Напиши, о чём напомнить.\n\n"
        "Можно сразу с датой — например: <i>«завтра в 15:00 встреча с врачом #работа»</i>.\n"
        "Или просто текст — дальше выберешь дату кнопками.",
        reply_markup=main_menu(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext) -> None:
    await state.clear()
    await msg.answer("❎ Отменено.", reply_markup=main_menu())


# ────── получение текста ──────

@router.message(Create.waiting_text, F.text)
async def got_text(msg: Message, state: FSMContext) -> None:
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    raw = msg.text.strip()
    text_no_tag, tag = extract_tag(raw)

    parsed = parse_when(text_no_tag, user.timezone)
    if parsed is not None:
        remind_utc, remainder = parsed
        reminder_text = remainder or text_no_tag or "Напоминание"
        if remind_utc <= datetime.utcnow():
            await msg.answer("⚠️ Эта дата уже прошла. Выбери другое время кнопками 👇")
        else:
            await state.update_data(text=reminder_text, tag=tag, remind_utc=remind_utc.isoformat())
            await state.set_state(Create.waiting_recurrence)
            await msg.answer(
                f"🗓 Понял: <b>{reminder_text}</b>\n"
                f"⏰ {_fmt_local(remind_utc, user.timezone)} ({user.timezone})\n\n"
                "Повторять?",
                reply_markup=build_recurrence(),
            )
            return

    # Без распознанной даты — сохраняем текст и идём в календарь
    await state.update_data(text=text_no_tag or "Напоминание", tag=tag)
    await state.set_state(Create.waiting_date)
    now = datetime.now(ZoneInfo(user.timezone))
    await msg.answer("📅 Выбери дату:", reply_markup=build_calendar(now.year, now.month, user.timezone))


# ────── календарь ──────

@router.callback_query(Create.waiting_date, F.data.startswith("cal:"))
async def on_calendar(cb: CallbackQuery, state: FSMContext) -> None:
    _, action, y, m, d = cb.data.split(":")
    y, m, d = int(y), int(m), int(d)
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username)

    if action == "ignore":
        await cb.answer()
        return
    if action in ("prev", "next"):
        delta = -1 if action == "prev" else 1
        new_month = m + delta
        new_year = y
        if new_month < 1:
            new_month, new_year = 12, y - 1
        elif new_month > 12:
            new_month, new_year = 1, y + 1
        await cb.message.edit_reply_markup(reply_markup=build_calendar(new_year, new_month, user.timezone))
        await cb.answer()
        return
    if action == "pick":
        await state.update_data(date=f"{y:04d}-{m:02d}-{d:02d}")
        await state.set_state(Create.waiting_time)
        await cb.message.edit_text(f"🕐 Дата: <b>{d:02d}.{m:02d}.{y}</b>\nВыбери время:",
                                   reply_markup=build_time())
        await cb.answer()


# ────── время (час + минуты за один шаг) ──────

@router.callback_query(Create.waiting_time, F.data.startswith("tm:"))
async def on_time(cb: CallbackQuery, state: FSMContext) -> None:
    _, h, mn = cb.data.split(":")
    hour, minute = int(h), int(mn)
    data = await state.get_data()
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username)
    y, m, d = map(int, data["date"].split("-"))
    local_dt = datetime(y, m, d, hour, minute, tzinfo=ZoneInfo(user.timezone))
    if local_dt <= datetime.now(ZoneInfo(user.timezone)):
        await cb.answer("⚠️ Это время уже прошло", show_alert=True)
        return
    remind_utc = local_dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    await state.update_data(remind_utc=remind_utc.isoformat())
    await state.set_state(Create.waiting_recurrence)
    await cb.message.edit_text(
        f"⏰ Время: <b>{local_dt.strftime('%d.%m.%Y %H:%M')}</b> ({user.timezone})\n\n"
        "Повторять?",
        reply_markup=build_recurrence(),
    )
    await cb.answer()


# ────── повтор ──────

@router.callback_query(Create.waiting_recurrence, F.data.startswith("rec:"))
async def on_recurrence(cb: CallbackQuery, state: FSMContext) -> None:
    rec = cb.data.split(":", 1)[1]
    await state.update_data(recurrence=rec)
    await state.set_state(Create.waiting_pre_notify)
    await cb.message.edit_text("🔔 Предварительное уведомление?", reply_markup=build_pre_notify())
    await cb.answer()


# ────── pre-notify ──────

@router.callback_query(Create.waiting_pre_notify, F.data.startswith("pre:"))
async def on_pre_notify(cb: CallbackQuery, state: FSMContext) -> None:
    minutes = int(cb.data.split(":")[1])
    await state.update_data(pre_notify=minutes)
    await state.set_state(Create.waiting_tag)
    data = await state.get_data()
    if data.get("tag"):
        # тег уже задан в тексте — пропускаем шаг
        await _finalize(cb, state)
        return
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username)
    user_tags = await list_tags(user.id)
    await cb.message.edit_text("🏷 Выбери тег (или без):", reply_markup=build_tags(user_tags))
    await cb.answer()


@router.callback_query(Create.waiting_tag, F.data.startswith("tag:"))
async def on_tag(cb: CallbackQuery, state: FSMContext) -> None:
    tag = cb.data.split(":", 1)[1]
    await state.update_data(tag=None if tag == "NONE" else tag)
    await _finalize(cb, state)


# ────── финал ──────

async def _finalize(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username)
    remind_utc = datetime.fromisoformat(data["remind_utc"])
    r = await add_reminder(
        user_id=user.id,
        text=data["text"],
        remind_at_utc=remind_utc,
        recurrence=data.get("recurrence", "none"),
        tag=data.get("tag"),
        pre_notify_minutes=data.get("pre_notify", 0),
    )
    await state.clear()
    tag_str = f" #{r.tag}" if r.tag else ""
    rec_str = "" if r.recurrence == "none" else f"\n🔁 {r.recurrence}"
    pre_str = "" if r.pre_notify_minutes == 0 else f"\n🔔 за {r.pre_notify_minutes} мин"
    await cb.message.edit_text(
        f"✅ Напоминание сохранено!\n\n"
        f"📝 <b>{r.text}</b>{tag_str}\n"
        f"⏰ {_fmt_local(r.remind_at, user.timezone)} ({user.timezone}){rec_str}{pre_str}\n\n"
        f"id: <code>{r.id}</code>"
    )
    await cb.answer("Сохранено ✅")
    logger.info(f"reminder #{r.id} created for user {user.telegram_id}")
