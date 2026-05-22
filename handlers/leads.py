"""Дашборд лидов: отчёт-воронка, список лидов, управление кодовыми словами.

Лидов ловит userbot (services/userbot.py). Здесь владелец отмечает этапы
(ответил / созвонился / купил / не купил) и смотрит сводку через /report.
"""
from html import escape

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database.db import (add_code_word, delete_code_word, delete_lead, get_lead,
                         get_or_create_user, list_code_words, list_leads, update_lead)
from keyboards.inline import code_words_kb, lead_card_actions

router = Router(name="leads")


class CodeWordFSM(StatesGroup):
    waiting_word = State()


# ────── отображение карточки лида ──────

def _outcome_label(lead) -> str:
    if lead.outcome == "bought":
        return "💰 купил"
    if lead.outcome == "not_bought":
        return "❌ не купил"
    return "⏳ в работе"


def _lead_text(lead) -> str:
    uname = f" @{escape(lead.contact_username)}" if lead.contact_username else ""
    stages = [
        "✅ ответил" if lead.answered else "▫️ не ответил",
        "✅ созвон" if lead.called else "▫️ нет созвона",
    ]
    return (
        f"🎯 <b>Лид #{lead.id}</b> · 🔑 {escape(lead.code_word)}\n"
        f"👤 {escape(lead.contact_name)}{uname}\n"
        f"💬 <i>{escape(lead.first_message[:200])}</i>\n"
        f"📊 {' · '.join(stages)} · {_outcome_label(lead)}"
    )


# ────── отчёт ──────

def _stats(leads) -> dict:
    return {
        "total": len(leads),
        "answered": sum(1 for l in leads if l.answered),
        "called": sum(1 for l in leads if l.called),
        "bought": sum(1 for l in leads if l.outcome == "bought"),
        "not_bought": sum(1 for l in leads if l.outcome == "not_bought"),
        "pending": sum(1 for l in leads if l.outcome == "pending"),
    }


def _block(title: str, st: dict) -> str:
    return (
        f"🔑 <b>{escape(title)}</b>\n"
        f"   Всего: {st['total']}\n"
        f"   💬 Ответили: {st['answered']}\n"
        f"   📞 Созвонились: {st['called']}\n"
        f"   💰 Купили: {st['bought']}\n"
        f"   ❌ Не купили: {st['not_bought']}\n"
        f"   ⏳ В работе: {st['pending']}"
    )


@router.message(Command("report"))
@router.message(F.text == "📊 Отчёт")
async def cmd_report(msg: Message) -> None:
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    leads = await list_leads(user.id)
    if not leads:
        await msg.answer(
            "📊 Пока нет лидов.\n\n"
            "Userbot начнёт их ловить, как только придут сообщения с кодовыми словами. "
            "Добавь слова через 🔑 Кодовые слова."
        )
        return

    by_word: dict[str, list] = {}
    for l in leads:
        by_word.setdefault(l.code_word, []).append(l)
    blocks = [_block(w, _stats(ls)) for w, ls in sorted(by_word.items())]
    total = _stats(leads)
    text = (
        "📊 <b>Отчёт по лидам</b>\n\n"
        + "\n\n".join(blocks)
        + "\n\n━━━━━━━━━━━\n"
        + f"<b>ИТОГО:</b> {total['total']} лидов\n"
        + f"💰 Купили: {total['bought']} · ❌ Не купили: {total['not_bought']}"
        + f" · ⏳ В работе: {total['pending']}"
    )
    await msg.answer(text)


# ────── список лидов ──────

@router.message(Command("leads"))
@router.message(F.text == "🎯 Лиды")
async def cmd_leads(msg: Message) -> None:
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    leads = await list_leads(user.id)
    if not leads:
        await msg.answer("🎯 Лидов пока нет.")
        return
    shown = leads[:10]
    await msg.answer(f"🎯 Последние лиды — {len(shown)} из {len(leads)}:")
    for lead in shown:
        await msg.answer(_lead_text(lead), reply_markup=lead_card_actions(lead))


@router.callback_query(F.data.startswith("lead:"))
async def on_lead_action(cb: CallbackQuery) -> None:
    _, action, raw_id = cb.data.split(":")
    lead_id = int(raw_id)
    lead = await get_lead(lead_id)
    if lead is None:
        await cb.answer("Лид не найден", show_alert=True)
        return

    if action == "del":
        await delete_lead(lead_id)
        await cb.message.edit_text(f"🗑 Лид #{lead_id} удалён.")
        await cb.answer("Удалено")
        return

    if action == "ans":
        await update_lead(lead_id, answered=not lead.answered)
    elif action == "call":
        await update_lead(lead_id, called=not lead.called)
    elif action == "buy":
        await update_lead(lead_id, outcome="bought")
    elif action == "nobuy":
        await update_lead(lead_id, outcome="not_bought")
    elif action == "reset":
        await update_lead(lead_id, outcome="pending")

    lead = await get_lead(lead_id)
    await cb.message.edit_text(_lead_text(lead), reply_markup=lead_card_actions(lead))
    await cb.answer("Обновлено")


# ────── кодовые слова ──────

@router.message(Command("codewords"))
@router.message(F.text == "🔑 Кодовые слова")
async def cmd_codewords(msg: Message) -> None:
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    words = await list_code_words(user.id)
    text = (
        "🔑 <b>Кодовые слова</b>\n\n"
        "Лид фиксируется автоматически, если входящее личное сообщение "
        "содержит одно из этих слов."
    )
    if not words:
        text += "\n\n<i>Список пуст — добавь первое слово.</i>"
    await msg.answer(text, reply_markup=code_words_kb(words))


@router.callback_query(F.data == "cw:ignore")
async def cw_ignore(cb: CallbackQuery) -> None:
    await cb.answer()


@router.callback_query(F.data == "cw:add")
async def cw_add(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CodeWordFSM.waiting_word)
    await cb.message.answer("✍️ Напиши кодовое слово (например: Chegirma).\n/cancel — отмена.")
    await cb.answer()


@router.message(CodeWordFSM.waiting_word, F.text)
async def cw_got_word(msg: Message, state: FSMContext) -> None:
    word = msg.text.strip()
    if not word or word.startswith("/"):
        await msg.answer("Это не похоже на слово. Попробуй ещё раз или /cancel.")
        return
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username)
    cw = await add_code_word(user.id, word)
    await state.clear()
    if cw is None:
        await msg.answer(f"⚠️ Слово «{escape(word)}» уже есть в списке.")
    else:
        await msg.answer(f"✅ Кодовое слово «{escape(word)}» добавлено.")
    words = await list_code_words(user.id)
    await msg.answer("🔑 <b>Кодовые слова</b>:", reply_markup=code_words_kb(words))


@router.callback_query(F.data.startswith("cw:del:"))
async def cw_del(cb: CallbackQuery) -> None:
    cw_id = int(cb.data.split(":")[2])
    await delete_code_word(cw_id)
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username)
    words = await list_code_words(user.id)
    await cb.message.edit_reply_markup(reply_markup=code_words_kb(words))
    await cb.answer("Удалено")
