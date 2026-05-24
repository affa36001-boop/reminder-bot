"""Inline-клавиатуры: календарь, выбор времени, повторение, теги, действия с напоминанием.

Callback-данные имеют префиксы:
- cal:<action>:<y>:<m>:<d>   — навигация по календарю и выбор дня
- hr:<H>                      — выбор часа
- mn:<M>                      — выбор минуты
- rec:<rule>                  — выбор повторения
- pre:<minutes>               — за сколько до события напомнить
- tag:<value>                 — выбор тега (NONE — без тега)
- act:<action>:<reminder_id>  — действия с напоминанием (done/del/snz10/snz60/snz1440/edit)
- nav:<screen>                — переход между экранами (cancel/confirm)
"""
import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

_RU_MONTHS = ["январь", "февраль", "март", "апрель", "май", "июнь",
              "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
_RU_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def build_calendar(year: int, month: int, tz_name: str | None = None) -> InlineKeyboardMarkup:
    """Месячный календарь. Прошедшие дни — заблокированы."""
    today = datetime.now(ZoneInfo(tz_name)).date() if tz_name else date.today()
    kb = InlineKeyboardBuilder()
    # шапка с месяцем и стрелками
    kb.row(
        InlineKeyboardButton(text="‹", callback_data=f"cal:prev:{year}:{month}:0"),
        InlineKeyboardButton(text=f"{_RU_MONTHS[month-1].capitalize()} {year}",
                             callback_data="cal:ignore:0:0:0"),
        InlineKeyboardButton(text="›", callback_data=f"cal:next:{year}:{month}:0"),
    )
    kb.row(*[InlineKeyboardButton(text=w, callback_data="cal:ignore:0:0:0") for w in _RU_WEEKDAYS])
    cal = calendar.Calendar(firstweekday=0)
    for week in cal.monthdatescalendar(year, month):
        row = []
        for d in week:
            if d.month != month:
                row.append(InlineKeyboardButton(text=" ", callback_data="cal:ignore:0:0:0"))
            elif d < today:
                row.append(InlineKeyboardButton(text="·", callback_data="cal:ignore:0:0:0"))
            else:
                mark = "•" if d == today else ""
                row.append(InlineKeyboardButton(text=f"{mark}{d.day}",
                                                callback_data=f"cal:pick:{d.year}:{d.month}:{d.day}"))
        kb.row(*row)
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="nav:cancel"))
    return kb.as_markup()


def build_time() -> InlineKeyboardMarkup:
    """Единый экран выбора времени: шаг 30 минут, 4 колонки."""
    kb = InlineKeyboardBuilder()
    for h in range(24):
        for m in (0, 30):
            kb.button(text=f"{h:02d}:{m:02d}", callback_data=f"tm:{h}:{m}")
    kb.adjust(4)
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="nav:cancel"))
    return kb.as_markup()


def build_recurrence() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    options = [
        ("Без повтора", "none"),
        ("Ежедневно", "daily"),
        ("Еженедельно", "weekly"),
        ("Ежемесячно", "monthly"),
        ("Ежегодно", "yearly"),
        ("Каждые 3 дня", "custom:3"),
    ]
    for label, val in options:
        kb.button(text=label, callback_data=f"rec:{val}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="nav:cancel"))
    return kb.as_markup()


def build_pre_notify() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    options = [("Не нужно", 0), ("За 10 минут", 10), ("За 1 час", 60),
               ("За 3 часа", 180), ("За день", 1440)]
    for label, val in options:
        kb.button(text=label, callback_data=f"pre:{val}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="nav:cancel"))
    return kb.as_markup()


def build_tags(user_tags: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚫 Без тега", callback_data="tag:NONE")
    for t in ["работа", "здоровье", "личное", "учёба", "финансы"]:
        kb.button(text=f"#{t}", callback_data=f"tag:{t}")
    for t in user_tags:
        if t not in {"работа", "здоровье", "личное", "учёба", "финансы"}:
            kb.button(text=f"#{t}", callback_data=f"tag:{t}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="nav:cancel"))
    return kb.as_markup()


def reminder_actions(reminder_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Выполнено", callback_data=f"act:done:{reminder_id}"),
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"act:del:{reminder_id}"),
    )
    kb.row(
        InlineKeyboardButton(text="⏰ +10 мин", callback_data=f"act:snz10:{reminder_id}"),
        InlineKeyboardButton(text="⏰ +1 ч", callback_data=f"act:snz60:{reminder_id}"),
        InlineKeyboardButton(text="⏰ +1 д", callback_data=f"act:snz1440:{reminder_id}"),
    )
    return kb.as_markup()


def list_item_actions(reminder_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅", callback_data=f"act:done:{reminder_id}"),
        InlineKeyboardButton(text="❌", callback_data=f"act:del:{reminder_id}"),
        InlineKeyboardButton(text="⏰ +1ч", callback_data=f"act:snz60:{reminder_id}"),
    )
    return kb.as_markup()


_TZ_OPTIONS = [
    ("Europe/Kaliningrad", "Калининград (UTC+2)"),
    ("Europe/Moscow", "Москва (UTC+3)"),
    ("Europe/Samara", "Самара (UTC+4)"),
    ("Asia/Yekaterinburg", "Екатеринбург (UTC+5)"),
    ("Asia/Omsk", "Омск (UTC+6)"),
    ("Asia/Krasnoyarsk", "Красноярск (UTC+7)"),
    ("Asia/Irkutsk", "Иркутск (UTC+8)"),
    ("Asia/Yakutsk", "Якутск (UTC+9)"),
    ("Asia/Vladivostok", "Владивосток (UTC+10)"),
    ("Asia/Almaty", "Алматы (UTC+5)"),
    ("Europe/Kyiv", "Киев (UTC+2/+3)"),
    ("Europe/Minsk", "Минск (UTC+3)"),
]


def build_timezone() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for tz, label in _TZ_OPTIONS:
        kb.button(text=label, callback_data=f"tz:{tz}")
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="nav:cancel"))
    return kb.as_markup()


def settings_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🌍 Часовой пояс", callback_data="settings:tz")
    kb.button(text="🏷 Мои теги", callback_data="settings:tags")
    kb.adjust(1)
    return kb.as_markup()
