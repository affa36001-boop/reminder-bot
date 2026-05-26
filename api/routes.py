from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from api.auth import validate_init_data
from config import settings
from database.db import (
    add_reminder, delete_reminder, get_or_create_user, get_reminder,
    list_active, list_tags, set_status,
)

router = APIRouter()


async def _auth(init_data: str):
    tg_user = validate_init_data(init_data, settings.bot_token)
    if tg_user is None:
        raise HTTPException(status_code=401, detail="Invalid initData")
    user = await get_or_create_user(tg_user["id"], tg_user.get("username"))
    return tg_user, user


class CreateBody(BaseModel):
    text: str
    remind_at: str          # ISO local datetime without tz, e.g. "2024-01-15T10:30"
    recurrence: str = "none"
    tag: str | None = None
    pre_notify_minutes: int = 0


@router.get("/reminders")
async def api_list(
    filter: str = "all",
    tag: str | None = None,
    x_telegram_init_data: str = Header(...),
):
    _, user = await _auth(x_telegram_init_data)
    tz = ZoneInfo(user.timezone)
    now_utc = datetime.utcnow()
    to_utc = None

    if filter == "today":
        now_local = datetime.now(tz)
        end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
        to_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    elif filter == "week":
        to_utc = now_utc + timedelta(days=7)

    items = await list_active(user.id, from_utc=now_utc, to_utc=to_utc, tag=tag or None)
    return {
        "timezone": user.timezone,
        "reminders": [
            {
                "id": r.id,
                "text": r.text,
                "remind_at": r.remind_at.isoformat(),
                "recurrence": r.recurrence,
                "tag": r.tag,
                "pre_notify_minutes": r.pre_notify_minutes,
            }
            for r in items
        ],
    }


@router.post("/reminders", status_code=201)
async def api_create(body: CreateBody, x_telegram_init_data: str = Header(...)):
    _, user = await _auth(x_telegram_init_data)
    tz = ZoneInfo(user.timezone)
    local_dt = datetime.fromisoformat(body.remind_at).replace(tzinfo=tz)
    utc_dt = local_dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    if utc_dt <= datetime.utcnow():
        raise HTTPException(400, "remind_at is in the past")
    r = await add_reminder(
        user_id=user.id,
        text=body.text,
        remind_at_utc=utc_dt,
        recurrence=body.recurrence,
        tag=body.tag,
        pre_notify_minutes=body.pre_notify_minutes,
    )
    return {"id": r.id}


@router.patch("/reminders/{rid}/done", status_code=204)
async def api_done(rid: int, x_telegram_init_data: str = Header(...)):
    _, user = await _auth(x_telegram_init_data)
    r = await get_reminder(rid)
    if r is None or r.user_id != user.id:
        raise HTTPException(404)
    await set_status(rid, "done")


@router.delete("/reminders/{rid}", status_code=204)
async def api_delete(rid: int, x_telegram_init_data: str = Header(...)):
    _, user = await _auth(x_telegram_init_data)
    r = await get_reminder(rid)
    if r is None or r.user_id != user.id:
        raise HTTPException(404)
    await delete_reminder(rid)


@router.get("/tags")
async def api_tags(x_telegram_init_data: str = Header(...)):
    _, user = await _auth(x_telegram_init_data)
    return await list_tags(user.id)
