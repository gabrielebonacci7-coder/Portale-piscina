"""Entry point FastAPI: monta i router e crea lo schema all'avvio."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from app import __version__
from app.api.routers import (
    annunci,
    auth,
    bagnini,
    candidature,
    foto,
    messaggi,
    piscine,
    recensioni,
    zone,
)
from app.core.config import BASE_DIR, settings
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
app.include_router(candidature.router)
app.include_router(foto.router)
app.include_router(messaggi.router)
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


# Le foto caricate dagli utenti. Sta prima del montaggio della PWA perché
# quello, essendo su "/", cattura tutto quello che resta.
CARTELLA_MEDIA = Path(settings.media_dir)
CARTELLA_MEDIA.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=CARTELLA_MEDIA), name="media")


# La PWA è servita dallo stesso processo dell'API: una sola porta da avviare,
# nessun problema di CORS e il service worker vede tutto sotto la stessa origine.
# Il montaggio va per ultimo: cattura ciò che non è già stato preso dalle rotte.
CARTELLA_WEB = BASE_DIR / "web"
if CARTELLA_WEB.is_dir():
    app.mount("/", StaticFiles(directory=CARTELLA_WEB, html=True), name="web")
