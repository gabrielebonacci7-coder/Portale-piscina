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
    # Su PostgreSQL una connessione ferma da ore può essere già stata chiusa
    # dall'altra parte: `pre_ping` la controlla invece di far fallire la prima
    # richiesta del mattino.
    pool_pre_ping=not _is_sqlite,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    """Impostazioni che SQLite non applica da solo, e che vanno date a ogni
    connessione perché non si ricordano fra una e l'altra."""
    if not _is_sqlite:
        return
    cursor = dbapi_connection.cursor()
    # Senza questo SQLite ignora del tutto le FOREIGN KEY.
    cursor.execute("PRAGMA foreign_keys=ON")
    # WAL: chi legge non aspetta chi scrive. Con il journal predefinito una
    # scrittura blocca tutte le letture, e con due bagnini che aggiornano la
    # bacheca mentre una piscina pubblica si arriva a "database is locked".
    cursor.execute("PRAGMA journal_mode=WAL")
    # Se comunque si incrociano, si aspetta cinque secondi invece di fallire
    # subito: quasi tutti i conflitti si risolvono in millisecondi.
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def get_db() -> Iterator[Session]:
    """Dipendenza FastAPI: apre una sessione per richiesta e la chiude sempre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
