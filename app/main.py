"""Entry point FastAPI: monta i router e crea lo schema all'avvio."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app import __version__
from app.api.routers import annunci, auth, bagnini, piscine, recensioni, zone
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import engine


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

# La PWA girerà su un'origine diversa dall'API: senza CORS il browser blocca.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bagnini.router)
app.include_router(piscine.router)
app.include_router(annunci.router)
app.include_router(recensioni.router)
app.include_router(zone.router)


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
