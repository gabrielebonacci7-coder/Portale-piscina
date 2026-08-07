"""Schemi Pydantic: validazione in ingresso e serializzazione in uscita."""

from app.schemas.annuncio import AnnuncioCreate, AnnuncioRead, AnnuncioUpdate, AutoreSintesi
from app.schemas.auth import CambioPassword, LoginRequest, RegistrazioneRequest, Token
from app.schemas.bagnino import (
    BrevettoCreate,
    BrevettoRead,
    DisponibilitaCreate,
    DisponibilitaRead,
    EsperienzaCreate,
    EsperienzaRead,
    ProfiloBagninoCreate,
    ProfiloBagninoRead,
    ProfiloBagninoSintesi,
    ProfiloBagninoUpdate,
)
from app.schemas.candidatura import (
    CandidatoSintesi,
    CandidaturaConAnnuncio,
    CandidaturaCreate,
    CandidaturaRead,
)
from app.schemas.pagina import Pagina
from app.schemas.piscina import ProfiloPiscinaCreate, ProfiloPiscinaRead, ProfiloPiscinaUpdate
from app.schemas.recensione import RecensioneCreate, RecensioneRead, RiepilogoRecensioni
from app.schemas.utente import UtenteCreate, UtenteRead
from app.schemas.zona import ZonaRead

__all__ = [
    "AnnuncioCreate",
    "AnnuncioRead",
    "AnnuncioUpdate",
    "AutoreSintesi",
    "BrevettoCreate",
    "BrevettoRead",
    "CambioPassword",
    "CandidatoSintesi",
    "CandidaturaConAnnuncio",
    "CandidaturaCreate",
    "CandidaturaRead",
    "DisponibilitaCreate",
    "DisponibilitaRead",
    "EsperienzaCreate",
    "EsperienzaRead",
    "LoginRequest",
    "Pagina",
    "ProfiloBagninoCreate",
    "ProfiloBagninoRead",
    "ProfiloBagninoSintesi",
    "ProfiloBagninoUpdate",
    "ProfiloPiscinaCreate",
    "ProfiloPiscinaRead",
    "ProfiloPiscinaUpdate",
    "RecensioneCreate",
    "RecensioneRead",
    "RegistrazioneRequest",
    "RiepilogoRecensioni",
    "Token",
    "UtenteCreate",
    "UtenteRead",
    "ZonaRead",
]
