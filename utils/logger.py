"""Настройка loguru: пишем в stdout и в файл с ротацией"""
import sys
from loguru import logger
from config import settings


def setup_logger() -> None:
    # На Windows консоль по умолчанию cp1252 — кириллица в логах ломает вывод
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    logger.remove()
    logger.add(sys.stdout, level=settings.log_level, colorize=True,
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                      "<level>{level: <8}</level> | "
                      "<cyan>{name}:{function}:{line}</cyan> - {message}")
    logger.add("logs/bot.log", level=settings.log_level, rotation="10 MB",
               retention="14 days", encoding="utf-8")
