"""ReplyKeyboard — главное меню под полем ввода"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo

from config import settings


def main_menu() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="➕ Создать"), KeyboardButton(text="📋 Мои напоминания")],
        [KeyboardButton(text="📅 На сегодня"), KeyboardButton(text="📆 На неделю")],
        [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="❓ Помощь")],
    ]
    if settings.webapp_url:
        rows.insert(0, [KeyboardButton(
            text="📱 Открыть приложение",
            web_app=WebAppInfo(url=settings.webapp_url),
        )])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или напишите напоминание…",
    )


def hide() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
