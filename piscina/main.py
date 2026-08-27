"""Punto di partenza: monta l'API e serve la PWA."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from piscina import __version__
from piscina.api.routers import prenotazioni, pubblico, staff
from piscina.core.config import settings
from piscina.db.init_db import init_db
from piscina.db.session import engine

log = logging.getLogger("piscina")

CARTELLA_WEB = Path(__file__).resolve().parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not settings.destinatari_staff:
        log.warning(
            "PISCINA_EMAIL_STAFF non è impostata: le prenotazioni non "
            "verranno inoltrate via email (si vedono comunque in /staff)."
        )
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Prenotazione di ombrelloni e lettini della Piscina Comunale di Ciampino.",
    lifespan=lifespan,
)

app.include_router(pubblico.router)
app.include_router(prenotazioni.router)
app.include_router(staff.router)


@app.get("/health", tags=["sistema"])
def health() -> dict:
    with engine.connect():
        pass
    return {"stato": "ok", "versione": __version__}


@app.get("/staff", include_in_schema=False)
def pagina_staff() -> FileResponse:
    """Il gestionale ha un indirizzo suo, da tenere fra i preferiti.

    È la stessa applicazione: i file statici qui sotto servono index.html solo
    sulle cartelle, e su /staff risponderebbero 404.
    """
    return FileResponse(CARTELLA_WEB / "index.html")


# La PWA sta sotto "/" e cattura tutto quello che resta: va montata per ultima.
# `html=True` fa servire index.html sia su "/" sia sui percorsi che non
# corrispondono a un file, così l'app si può aprire direttamente su /staff.
app.mount("/", StaticFiles(directory=CARTELLA_WEB, html=True), name="pwa")
