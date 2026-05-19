"""Настройки: часовой пояс и просмотр тегов — всё через inline-кнопки"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database.db import get_or_create_user, list_tags, set_user_timezone
from keyboards.inline import build_timezone, settings_menu
from keyboards.reply import main_menu

router = Router(name="settings")


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def cmd_settings(msg: Message) -> None:
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    await msg.answer(
        f"⚙️ <b>Настройки</b>\n\n🌍 Часовой пояс: <b>{user.timezone}</b>",
        reply_markup=settings_menu(),
    )


@router.message(Command("timezone"))
async def cmd_timezone(msg: Message) -> None:
    await msg.answer("🌍 Выбери часовой пояс:", reply_markup=build_timezone())


@router.callback_query(F.data == "settings:tz")
async def on_tz_menu(cb: CallbackQuery) -> None:
    await cb.message.edit_text("🌍 Выбери часовой пояс:", reply_markup=build_timezone())
    await cb.answer()


@router.callback_query(F.data.startswith("tz:"))
async def on_tz_pick(cb: CallbackQuery) -> None:
    tz = cb.data.split(":", 1)[1]
    await set_user_timezone(cb.from_user.id, tz)
    await cb.message.edit_text(f"✅ Часовой пояс установлен: <b>{tz}</b>")
    await cb.answer("Сохранено")


@router.callback_query(F.data == "settings:tags")
async def on_tags_menu(cb: CallbackQuery) -> None:
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username)
    tags = await list_tags(user.id)
    if not tags:
        text = "🏷 У тебя пока нет тегов. Добавь #тег при создании напоминания."
    else:
        text = "🏷 Твои активные теги:\n\n" + "\n".join(f"• #{t}" for t in tags)
    await cb.message.edit_text(text)
    await cb.answer()
