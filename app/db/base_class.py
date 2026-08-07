"""Classe base dichiarativa e mixin comuni a tutti i modelli."""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db.types import UTCDateTime


def utcnow() -> datetime:
    """Timestamp timezone-aware, usato come default lato Python."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base dichiarativa: da qui eredita ogni tabella."""


class TimestampMixin:
    """Aggiunge le colonne di audit `creato_il` / `aggiornato_il`."""

    creato_il: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, server_default=func.now(), nullable=False
    )
    aggiornato_il: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
        nullable=False,
    )
