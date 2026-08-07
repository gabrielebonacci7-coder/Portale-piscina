"""Entry point FastAPI.

In questa fase l'app non espone ancora endpoint di dominio: serve a creare lo
schema all'avvio e a verificare che il database sia raggiungibile.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import engine, get_db
from app.models import Zona
from app.schemas import ZonaRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Comodo in sviluppo. In produzione lo schema lo gestiranno le migrazioni.
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Bacheca annunci per bagnini e strutture natatorie.",
    lifespan=lifespan,
)


@app.get("/health", tags=["sistema"])
def health() -> dict:
    """Stato del servizio e connessione al database."""
    with engine.connect():
        pass
    return {"stato": "ok", "versione": __version__}


@app.get("/schema", tags=["sistema"])
def schema_db() -> dict:
    """Elenco di tabelle e colonne: utile per ispezionare la struttura dati."""
    inspector = inspect(engine)
    return {
        tabella: [c["name"] for c in inspector.get_columns(tabella)]
        for tabella in sorted(inspector.get_table_names())
    }


@app.get("/zone", response_model=list[ZonaRead], tags=["anagrafiche"])
def elenco_zone(db: Session = Depends(get_db)) -> list[Zona]:
    """Zone disponibili per i filtri della bacheca."""
    return list(db.query(Zona).order_by(Zona.citta, Zona.nome).all())
