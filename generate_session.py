"""Одноразовый скрипт: генерирует строку сессии Telethon для userbot'а.

Запусти локально:  python generate_session.py
Введи номер телефона (в формате +998...) и код из Telegram.
Скрипт напечатает строку TELETHON_SESSION — скопируй её в .env.
Номер и код нигде не сохраняются.
"""
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()


def main() -> None:
    api_id = os.getenv("API_ID") or input("API_ID: ").strip()
    api_hash = os.getenv("API_HASH") or input("API_HASH: ").strip()

    with TelegramClient(StringSession(), int(api_id), api_hash) as client:
        session = client.session.save()
        print("\n=== TELETHON_SESSION ===")
        print(session)
        print("========================")
        print("Скопируй строку выше в .env как TELETHON_SESSION=...")


if __name__ == "__main__":
    main()
