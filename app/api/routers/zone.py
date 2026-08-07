"""Anagrafica delle zone, usata dai filtri della bacheca."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.models import Zona
from app.schemas.zona import ZonaRead

router = APIRouter(prefix="/zone", tags=["anagrafiche"])


@router.get("", response_model=list[ZonaRead])
def elenco_zone(db: DbSession, citta: str | None = None):
    query = select(Zona).order_by(Zona.citta, Zona.nome)
    if citta:
        query = query.where(Zona.citta == citta)
    return list(db.scalars(query))
