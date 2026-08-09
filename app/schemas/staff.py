"""Schemi del pannello di gestione.

Sono separati da quelli pubblici apposta: qui escono campi che in bacheca non
si vedono (email, stato dell'account, chi ha fatto cosa). Se riusassimo
`UtenteRead` o `BrevettoRead` basterebbe un'aggiunta distratta per far filtrare
un dato riservato in una risposta pubblica.
"""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Ruolo, TipoAzioneStaff, TipoBrevetto, TipoUtente
from app.schemas.common import ORMModel


class Riepilogo(BaseModel):
    """I numeri della prima schermata: quanto lavoro c'è in coda."""

    utenti: int
    bagnini: int
    piscine: int
    sospesi: int
    brevetti_da_verificare: int
    utenti_da_verificare: int
    annunci_aperti: int


class UtenteStaff(ORMModel):
    """Scheda di un account vista da chi gestisce la piattaforma."""

    id: int
    email: EmailStr
    telefono: str | None = None
    tipo: TipoUtente
    ruolo: Ruolo
    attivo: bool
    email_verificata: bool
    verificato: bool
    creato_il: datetime

    nome: str | None = None
    # Solo per i bagnini: quanti brevetti ha e quanti ne restano da controllare.
    brevetti: int = 0
    brevetti_da_verificare: int = 0


class BrevettoStaff(BaseModel):
    """Un brevetto in coda di verifica, con chi lo ha caricato."""

    id: int
    tipo: TipoBrevetto
    ente: str
    numero: str | None = None
    data_rilascio: date | None = None
    data_scadenza: date | None = None
    verificato: bool
    valido: bool

    bagnino_id: int
    utente_id: int
    nome: str
    email: EmailStr


class VerificaRequest(BaseModel):
    """Corpo comune a tutte le azioni che accendono o spengono un flag."""

    valore: bool = True
    motivo: str | None = Field(default=None, max_length=500)


class SospensioneRequest(BaseModel):
    attivo: bool
    motivo: str | None = Field(default=None, max_length=500)


class AzioneStaffRead(ORMModel):
    id: int
    staff_email: EmailStr
    azione: TipoAzioneStaff
    oggetto_tipo: str
    oggetto_id: int
    oggetto_etichetta: str | None = None
    motivo: str | None = None
    creato_il: datetime
