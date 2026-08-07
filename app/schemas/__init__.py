"""Schemi Pydantic: validazione in ingresso e serializzazione in uscita."""

from app.schemas.annuncio import AnnuncioCreate, AnnuncioRead, AnnuncioUpdate
from app.schemas.bagnino import (
    BrevettoCreate,
    BrevettoRead,
    DisponibilitaCreate,
    DisponibilitaRead,
    EsperienzaCreate,
    EsperienzaRead,
    ProfiloBagninoCreate,
    ProfiloBagninoRead,
)
from app.schemas.piscina import ProfiloPiscinaCreate, ProfiloPiscinaRead
from app.schemas.recensione import RecensioneCreate, RecensioneRead
from app.schemas.utente import UtenteCreate, UtenteRead
from app.schemas.zona import ZonaRead

__all__ = [
    "AnnuncioCreate",
    "AnnuncioRead",
    "AnnuncioUpdate",
    "BrevettoCreate",
    "BrevettoRead",
    "DisponibilitaCreate",
    "DisponibilitaRead",
    "EsperienzaCreate",
    "EsperienzaRead",
    "ProfiloBagninoCreate",
    "ProfiloBagninoRead",
    "ProfiloPiscinaCreate",
    "ProfiloPiscinaRead",
    "RecensioneCreate",
    "RecensioneRead",
    "UtenteCreate",
    "UtenteRead",
    "ZonaRead",
]
