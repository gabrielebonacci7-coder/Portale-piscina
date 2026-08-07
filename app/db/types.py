"""Tipi di colonna personalizzati."""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """DateTime sempre timezone-aware in UTC.

    SQLite non memorizza il fuso orario: senza questo tipo un datetime salvato
    aware tornerebbe naive dalla query, e confrontarlo con `datetime.now(utc)`
    solleverebbe TypeError. Qui si converte a UTC in scrittura e si riattacca
    `tzinfo=UTC` in lettura, così il resto del codice lavora sempre aware.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            # Un datetime senza fuso lo interpretiamo come UTC, non come ora locale.
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
