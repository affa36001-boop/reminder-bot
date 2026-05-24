"""Стартовые команды: /start, /help, кнопка Помощь"""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from database.db import get_or_create_user
from keyboards.reply import main_menu

router = Router(name="start")


HELP_TEXT = (
    "👋 <b>Привет!</b> Я — твой персональный помощник-напоминалка.\n\n"
    "🔘 Пользуйся кнопками снизу — почти всё делается в пару тапов.\n\n"
    "<b>Что я умею:</b>\n"
    "• ➕ <b>Создать</b> — пошагово через календарь или одной строкой\n"
    "  (например: «завтра в 15:00 встреча #работа»)\n"
    "• 📋 <b>Мои напоминания</b> — все активные с кнопками управления\n"
    "• 📅 <b>На сегодня</b> / 📆 <b>На неделю</b> — фильтры по времени\n"
    "• ⚙️ <b>Настройки</b> — часовой пояс, теги\n\n"
    "🔁 Повторение, 🏷 теги и ⏰ предварительные уведомления настраиваются при создании.\n\n"
    "Команды: /list, /today, /week, /cancel, /help."
)


@router.message(CommandStart())
async def cmd_start(msg: Message) -> None:
    await get_or_create_user(msg.from_user.id, msg.from_user.username)
    await msg.answer(HELP_TEXT, reply_markup=main_menu())


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(msg: Message) -> None:
    await msg.answer(HELP_TEXT, reply_markup=main_menu())
