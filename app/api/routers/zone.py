"""Anagrafica delle zone, usata dai filtri della bacheca."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.init_db import ORDINE_AREE
from app.models import Zona
from app.schemas.zona import ZonaRead

router = APIRouter(prefix="/zone", tags=["anagrafiche"])


@router.get("", response_model=list[ZonaRead])
def elenco_zone(db: DbSession, area: str | None = None, citta: str | None = None):
    """Zone disponibili, raggruppate per area (Roma, Castelli Romani, ...)."""
    query = select(Zona)
    if area:
        query = query.where(Zona.area == area)
    if citta:
        query = query.where(Zona.citta == citta)

    zone = list(db.scalars(query))
    # Si ordina in Python per rispettare l'ordine dichiarato delle aree
    # (Roma per prima), che nel database non è ricavabile.
    posizione = {nome: i for i, nome in enumerate(ORDINE_AREE)}
    zone.sort(key=lambda z: (posizione.get(z.area, 99), z.nome))
    return zone
