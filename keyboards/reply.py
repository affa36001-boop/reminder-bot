"""ReplyKeyboard — главное меню под полем ввода"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def main_menu() -> ReplyKeyboardMarkup:
    """Меню бота-напоминалки."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать"), KeyboardButton(text="📋 Мои напоминания")],
            [KeyboardButton(text="📅 На сегодня"), KeyboardButton(text="📆 На неделю")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или напишите напоминание…",
    )


def leads_menu() -> ReplyKeyboardMarkup:
    """Меню бота учёта лидов."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Лиды"), KeyboardButton(text="📊 Отчёт")],
            [KeyboardButton(text="🔑 Кодовые слова"), KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие…",
    )


def hide() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
