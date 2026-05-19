"""Парсер дат и времени из свободного текста.

Поддерживается:
- абсолютный формат DD.MM.YYYY HH:MM
- относительный "через 2 часа", "через 15 минут", "через 3 дня"
- естественный язык через dateparser ("завтра в 15:00", "в пятницу в 9")
"""
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import dateparser


_REL_RE = re.compile(r"через\s+(\d+)\s+(минут|мин|часов|часа|час|дней|дня|день|недел[июя])",
                     re.IGNORECASE)


def _from_relative(text: str, now_local: datetime) -> datetime | None:
    m = _REL_RE.search(text)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2).lower()
    if unit.startswith("мин"):
        delta = timedelta(minutes=n)
    elif unit.startswith("час"):
        delta = timedelta(hours=n)
    elif unit.startswith("ден") or unit.startswith("дн"):
        delta = timedelta(days=n)
    elif unit.startswith("недел"):
        delta = timedelta(weeks=n)
    else:
        return None
    return now_local + delta


def parse_when(text: str, tz_name: str) -> tuple[datetime, str] | None:
    """Возвращает (UTC datetime, остаток текста) или None если не распознали"""
    tz = ZoneInfo(tz_name)
    now_local = datetime.now(tz)

    rel = _from_relative(text, now_local)
    if rel is not None:
        remainder = _REL_RE.sub("", text, count=1).strip(" ,.-")
        return rel.astimezone(ZoneInfo("UTC")).replace(tzinfo=None), remainder

    # Пробуем абсолютный формат "DD.MM.YYYY HH:MM"
    m = re.search(r"(\d{1,2}\.\d{1,2}\.\d{2,4}\s+\d{1,2}:\d{2})", text)
    if m:
        try:
            dt = datetime.strptime(m.group(1), "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                dt = datetime.strptime(m.group(1), "%d.%m.%y %H:%M")
            except ValueError:
                dt = None
        if dt:
            dt = dt.replace(tzinfo=tz)
            remainder = text.replace(m.group(1), "").strip(" ,.-")
            return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None), remainder

    # Универсальный парсер dateparser
    parsed = dateparser.parse(
        text,
        languages=["ru", "en"],
        settings={"TIMEZONE": tz_name, "RETURN_AS_TIMEZONE_AWARE": True,
                  "PREFER_DATES_FROM": "future", "RELATIVE_BASE": now_local.replace(tzinfo=None)},
    )
    if parsed:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)
        return parsed.astimezone(ZoneInfo("UTC")).replace(tzinfo=None), text

    return None


def extract_tag(text: str) -> tuple[str, str | None]:
    """Извлекает первый #тег из текста и возвращает (text_without_tag, tag)"""
    m = re.search(r"#(\w+)", text)
    if not m:
        return text, None
    tag = m.group(1)
    cleaned = (text[:m.start()] + text[m.end():]).strip()
    return cleaned, tag


def next_occurrence(current_utc: datetime, recurrence: str) -> datetime | None:
    """Считает следующее срабатывание для повторяющегося напоминания"""
    if recurrence == "none" or not recurrence:
        return None
    if recurrence == "daily":
        return current_utc + timedelta(days=1)
    if recurrence == "weekly":
        return current_utc + timedelta(weeks=1)
    if recurrence == "monthly":
        # упрощение: +30 дней (для точного календарного шага нужно dateutil.relativedelta)
        return current_utc + timedelta(days=30)
    if recurrence == "yearly":
        return current_utc + timedelta(days=365)
    if recurrence.startswith("custom:"):
        try:
            n = int(recurrence.split(":", 1)[1])
            return current_utc + timedelta(days=n)
        except ValueError:
            return None
    return None
