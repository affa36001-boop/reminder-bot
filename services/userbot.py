"""Userbot на Telethon: ловит лидов по кодовым словам во входящих ЛС.

Работает под личным аккаунтом владельца. Когда во входящем личном сообщении
встречается одно из зарегистрированных кодовых слов — создаётся карточка лида,
а владельцу приходит уведомление с кнопками статусов в бота учёта лидов.

Если API-ключи, сессия или токен бота лидов не заданы — модуль не запускается.
"""
from html import escape

from aiogram import Bot
from loguru import logger
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from config import settings
from database.db import add_lead, get_or_create_user, lead_exists, list_code_words
from keyboards.inline import lead_card_actions


def _match_code_word(text: str, words: list[str]) -> str | None:
    low = text.lower()
    for w in words:
        if w.lower() in low:
            return w
    return None


async def run_userbot(leads_bot: Bot) -> None:
    """Запускает Telethon-клиент и шлёт карточки лидов в бот учёта лидов."""
    client = TelegramClient(
        StringSession(settings.telethon_session),
        settings.api_id,
        settings.api_hash,
    )
    await client.connect()
    if not await client.is_user_authorized():
        logger.error("Userbot: сессия недействительна — запусти generate_session.py заново")
        return

    me = await client.get_me()
    owner = await get_or_create_user(me.id, me.username)
    logger.info(f"Userbot запущен как {me.first_name} (id={me.id})")

    @client.on(events.NewMessage(incoming=True))
    async def on_incoming(event) -> None:
        if not event.is_private:
            return
        text = event.raw_text or ""
        if not text:
            return
        words = [cw.word for cw in await list_code_words(owner.id)]
        matched = _match_code_word(text, words) if words else None
        if matched is None:
            return

        sender = await event.get_sender()
        if sender is None or getattr(sender, "bot", False):
            return
        if await lead_exists(owner.id, sender.id):
            return

        name = " ".join(filter(None, [getattr(sender, "first_name", "") or "",
                                      getattr(sender, "last_name", "") or ""])).strip()
        name = name or "Без имени"
        username = getattr(sender, "username", None)
        lead = await add_lead(owner.id, matched, sender.id, name, username, text[:500])
        logger.info(f"Новый лид #{lead.id} по слову '{matched}' от {name}")

        uname = f" @{username}" if username else ""
        try:
            await leads_bot.send_message(
                me.id,
                f"🎯 <b>Новый лид!</b>\n\n"
                f"🔑 Кодовое слово: <b>{escape(matched)}</b>\n"
                f"👤 {escape(name)}{escape(uname)}\n"
                f"💬 <i>{escape(text[:200])}</i>",
                reply_markup=lead_card_actions(lead),
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление о лиде #{lead.id}: {e}")

    await client.run_until_disconnected()
