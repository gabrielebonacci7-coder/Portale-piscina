"""Registrazione, accesso, conferma dell'email, password dimenticata."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from reformer.api.deps import regole, utente_corrente
from reformer.core import limiti
from reformer.core.config import settings
from reformer.core.security import crea_token
from reformer.db.session import get_db
from reformer.models import Utente
from reformer.servizi import account, viste

router = APIRouter(prefix="/api/auth", tags=["accesso"])


class Registrazione(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    cognome: str = Field(min_length=1, max_length=80)
    telefono: str = Field(min_length=6, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    privacy: bool

    @field_validator("privacy")
    @classmethod
    def privacy_accettata(cls, v: bool) -> bool:
        if not v:
            raise ValueError("serve accettare l'informativa sulla privacy")
        return v


class Credenziali(BaseModel):
    email: EmailStr
    password: str = Field(max_length=200)


class Codice(BaseModel):
    codice: str = Field(min_length=10, max_length=200)


class SoloEmail(BaseModel):
    email: EmailStr


class NuovaPassword(BaseModel):
    codice: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=8, max_length=72)


def _sessione(utente: Utente) -> dict:
    return {"token": crea_token(utente.id, utente.sessione), "utente": viste.utente(utente)}


@router.post("/registrati", status_code=201)
def registrati(dati: Registrazione, request: Request, db: Session = Depends(get_db)) -> dict:
    limiti.controlla(
        f"registrazione:{limiti.ip_richiedente(request)}", settings.max_registrazioni_per_ip,
        "Troppe registrazioni da questa rete: riprova fra un'ora.",
    )
    with regole():
        utente = account.registra(
            db, nome=dati.nome, cognome=dati.cognome, telefono=dati.telefono,
            email=dati.email, password=dati.password,
        )
    return _sessione(utente)


@router.post("/accedi")
def accedi(dati: Credenziali, request: Request, db: Session = Depends(get_db)) -> dict:
    chiave = f"accesso:{limiti.ip_richiedente(request)}"
    limiti.controlla(chiave, settings.max_accessi, "Troppi tentativi: riprova fra un'ora.")
    with regole():
        utente = account.accedi(db, dati.email, dati.password)
    limiti.azzera(chiave)
    return _sessione(utente)


@router.post("/conferma")
def conferma(dati: Codice, db: Session = Depends(get_db)) -> dict:
    with regole():
        utente = account.conferma_email(db, dati.codice)
    return _sessione(utente)


@router.post("/reinvia-conferma", status_code=204)
def reinvia_conferma(
    request: Request, utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)
) -> None:
    limiti.controlla(
        f"email:{limiti.ip_richiedente(request)}", settings.max_email_per_ip,
        "Hai già chiesto parecchi link: controlla anche nello spam, e riprova fra un'ora.",
    )
    account.invia_verifica(db, utente)


@router.post("/recupero", status_code=204)
def recupero(dati: SoloEmail, request: Request, db: Session = Depends(get_db)) -> None:
    limiti.controlla(
        f"email:{limiti.ip_richiedente(request)}", settings.max_email_per_ip,
        "Hai già chiesto parecchi link: controlla anche nello spam, e riprova fra un'ora.",
    )
    account.chiedi_recupero(db, dati.email)


@router.post("/nuova-password")
def nuova_password(dati: NuovaPassword, db: Session = Depends(get_db)) -> dict:
    with regole():
        utente = account.nuova_password(db, dati.codice, dati.password)
    return _sessione(utente)
