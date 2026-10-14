"""Quello che serve all'app prima ancora di accedere."""

from fastapi import APIRouter

from reformer import __version__
from reformer.dominio import orario
from reformer.servizi import viste

router = APIRouter(prefix="/api", tags=["pubblico"])


@router.get("/info")
def info() -> dict:
    return {
        "nome": "RE FORMER",
        "versione": __version__,
        "istruttrici": list(orario.ISTRUTTRICI.values()),
        "orario": [
            {
                "giorno": g,
                "nome": orario.GIORNI[g],
                "ore": [f"{t:%H:%M}" for t in ore],
                "istruttrice": orario.ISTRUTTRICE_DEL_GIORNO[g],
            }
            for g, ore in orario.ORARIO.items()
        ],
        "regole": viste.regole(),
        "oggi": orario.oggi().isoformat(),
        "fuso": orario.FUSO.key,
    }
