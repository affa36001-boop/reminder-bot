"""SQLAlchemy-модели: пользователи и напоминания"""
from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Boolean, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reminders: Mapped[list["Reminder"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    code_words: Mapped[list["CodeWord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    leads: Mapped[list["Lead"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    # UTC-время следующего срабатывания
    remind_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    # Повторение: none / daily / weekly / monthly / yearly / custom:N (каждые N дней)
    recurrence: Mapped[str] = mapped_column(String(32), default="none")
    tag: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # За сколько минут до события прислать предварительное уведомление (0 — не слать)
    pre_notify_minutes: Mapped[int] = mapped_column(Integer, default=0)
    pre_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    # active / done / missed
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="reminders")


class CodeWord(Base):
    """Кодовое слово рекламной кампании. Лид фиксируется, если входящее сообщение его содержит."""
    __tablename__ = "code_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    word: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="code_words")


class Lead(Base):
    """Лид, пойманный userbot'ом по кодовому слову во входящих ЛС."""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_word: Mapped[str] = mapped_column(String(64), index=True)
    contact_id: Mapped[int] = mapped_column(BigInteger, index=True)
    contact_name: Mapped[str] = mapped_column(String(128))
    contact_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_message: Mapped[str] = mapped_column(Text)
    # этапы воронки — независимые флаги
    answered: Mapped[bool] = mapped_column(Boolean, default=False)
    called: Mapped[bool] = mapped_column(Boolean, default=False)
    # pending / bought / not_bought
    outcome: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="leads")
