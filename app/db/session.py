"""Engine, session factory e dipendenza FastAPI per l'accesso al database."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    # SQLite + FastAPI: le richieste possono girare su thread diversi.
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    """SQLite ignora le FOREIGN KEY se non le si abilita a ogni connessione."""
    if not _is_sqlite:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db() -> Iterator[Session]:
    """Dipendenza FastAPI: apre una sessione per richiesta e la chiude sempre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
