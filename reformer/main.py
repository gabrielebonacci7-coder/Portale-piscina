"""Punto di partenza: monta l'API e serve la PWA.

    uvicorn reformer.main:app --reload --port 8002
"""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from reformer import __version__
from reformer.api.routers import auth, cliente, pubblico, staff
from reformer.core.config import settings
from reformer.db.init_db import init_db
from reformer.db.session import engine
from reformer.servizi import promemoria

log = logging.getLogger("reformer")

CARTELLA_WEB = Path(__file__).resolve().parent / "web"


def controlla_configurazione() -> None:
    """Online non si parte con la configurazione di sviluppo.

    Meglio un'app che non si accende, con un messaggio chiaro nel log, che
    un'app accesa con la chiave segreta scritta su GitHub.
    """
    if settings.debug:
        return
    problemi = []
    if settings.chiave_di_sviluppo:
        problemi.append("REFORMER_SECRET_KEY è quella di sviluppo: generane una nuova")
    if settings.url_pubblico.startswith("http://127.0.0.1"):
        problemi.append("REFORMER_URL_PUBBLICO è ancora l'indirizzo locale: i link nelle email non funzionerebbero")
    if problemi:
        raise RuntimeError("Configurazione non pronta per andare online:\n- " + "\n- ".join(problemi))
    if not settings.email_smtp_host:
        log.warning("REFORMER_EMAIL_SMTP_HOST non impostato: le email finiscono solo nel log.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    controlla_configurazione()
    init_db()
    giro = asyncio.create_task(promemoria.giro_continuo()) if settings.promemoria_attivi else None
    yield
    if giro:
        giro.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await giro


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Prenotazione delle lezioni di pilates reformer con Greta ed Elisa.",
    lifespan=lifespan,
)

app.include_router(pubblico.router)
app.include_router(auth.router)
app.include_router(cliente.router)
app.include_router(staff.router)


@app.get("/health", tags=["sistema"])
def health() -> dict:
    with engine.connect():
        pass
    return {"stato": "ok", "versione": __version__}


# La PWA sta sotto "/" e cattura tutto quello che resta: va montata per ultima.
app.mount("/", StaticFiles(directory=CARTELLA_WEB, html=True), name="pwa")
