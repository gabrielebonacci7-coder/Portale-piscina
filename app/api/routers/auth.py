"""Registrazione, login e gestione del proprio account."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, verify_password
from app.crud import utente as crud_utente
from app.schemas.auth import CambioPassword, LoginRequest, RegistrazioneRequest, Token
from app.schemas.utente import UtenteRead

router = APIRouter(prefix="/auth", tags=["autenticazione"])


@router.post("/registrazione", response_model=UtenteRead, status_code=status.HTTP_201_CREATED)
def registrazione(dati: RegistrazioneRequest, db: DbSession):
    """Crea un account. Il profilo (bagnino o piscina) si crea subito dopo."""
    if crud_utente.get_by_email(db, dati.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email già registrata")
    return crud_utente.crea_utente(db, dati)


@router.post("/login", response_model=Token)
def login(dati: LoginRequest, db: DbSession):
    """Login in JSON. Restituisce il token da usare come `Bearer`."""
    utente = crud_utente.autentica(db, dati.email, dati.password)
    if utente is None:
        # Messaggio volutamente generico: non si rivela se l'email esiste.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o password non corretti")
    if not utente.attivo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disattivato")
    return Token(access_token=create_access_token(utente.id), utente=utente)


@router.post("/token", response_model=Token, include_in_schema=False)
def login_form(db: DbSession, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Stessa cosa in formato form OAuth2: serve al pulsante Authorize di /docs."""
    utente = crud_utente.autentica(db, form.username, form.password)
    if utente is None or not utente.attivo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o password non corretti")
    return Token(access_token=create_access_token(utente.id), utente=utente)


@router.get("/me", response_model=UtenteRead)
def utente_corrente(utente: CurrentUser):
    """Dati dell'account collegato al token."""
    return utente


@router.post("/cambio-password", status_code=status.HTTP_204_NO_CONTENT)
def cambio_password(dati: CambioPassword, utente: CurrentUser, db: DbSession):
    if not verify_password(dati.password_attuale, utente.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password attuale non corretta")
    crud_utente.cambia_password(db, utente, dati.password_nuova)
