"""Engine, session factory e dipendenza FastAPI per l'accesso al database."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from piscina.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=not _is_sqlite,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(Engine, "connect")
def _pragma_sqlite(dbapi_connection, connection_record) -> None:
    """Impostazioni che SQLite non applica da solo e che vanno ridate a ogni
    connessione."""
    if not _is_sqlite:
        return
    cursor = dbapi_connection.cursor()
    # Senza questo SQLite ignora del tutto le FOREIGN KEY.
    cursor.execute("PRAGMA foreign_keys=ON")
    # WAL: chi legge la mappa non aspetta chi sta prenotando.
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
