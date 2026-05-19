"""Обработка inline-кнопок над напоминаниями: Выполнено / Удалить / Отложить.

Используется и для уведомлений, и для пунктов в списке.
"""
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from loguru import logger

from database.db import delete_reminder, get_reminder, reschedule, set_status

router = Router(name="callbacks")


@router.callback_query(F.data.startswith("act:"))
async def on_action(cb: CallbackQuery) -> None:
    _, action, rid_str = cb.data.split(":")
    rid = int(rid_str)
    r = await get_reminder(rid)
    if r is None:
        await cb.answer("Напоминание уже удалено", show_alert=True)
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    if action == "done":
        await set_status(rid, "done")
        await cb.message.edit_text(f"✅ Выполнено: {r.text}")
        await cb.answer("Отмечено как выполненное")
        logger.info(f"reminder #{rid} marked done")
        return

    if action == "del":
        await delete_reminder(rid)
        await cb.message.edit_text(f"❌ Удалено: {r.text}")
        await cb.answer("Удалено")
        logger.info(f"reminder #{rid} deleted")
        return

    if action.startswith("snz"):
        minutes = int(action[3:])
        new_utc = max(datetime.utcnow(), r.remind_at) + timedelta(minutes=minutes)
        await reschedule(rid, new_utc)
        await set_status(rid, "active")
        human = {10: "10 минут", 60: "1 час", 1440: "1 день"}.get(minutes, f"{minutes} мин")
        await cb.message.edit_text(f"⏰ Отложено на {human}: {r.text}\nНовое время: "
                                   f"{new_utc.strftime('%d.%m %H:%M')} UTC")
        await cb.answer(f"Отложено на {human}")
        logger.info(f"reminder #{rid} snoozed by {minutes} min")
        return


@router.callback_query(F.data == "nav:cancel")
async def on_cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await cb.message.edit_text("❎ Отменено.")
    except Exception:
        pass
    await cb.answer()
