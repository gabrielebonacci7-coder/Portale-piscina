"""Dipendenze riusabili dai router: sessione, utente autenticato, controlli di ruolo."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import ProfiloBagnino, ProfiloPiscina, TipoUtente, Utente

# `tokenUrl` serve al pulsante "Authorize" di /docs, che invia un form:
# punta quindi a /auth/token, non a /auth/login che invece accetta JSON.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Starlette ha rinominato la costante 422 (UNPROCESSABLE_ENTITY ->
# UNPROCESSABLE_CONTENT): si usa il numero per non dipendere dalla versione.
HTTP_422_DATI_NON_VALIDI = 422
HTTP_413_FILE_TROPPO_GRANDE = 413

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> Utente:
    """Risolve il token nell'utente corrispondente."""
    credenziali_non_valide = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide o token scaduto",
        headers={"WWW-Authenticate": "Bearer"},
    )

    utente_id = decode_access_token(token)
    if utente_id is None:
        raise credenziali_non_valide

    utente = db.get(Utente, utente_id)
    if utente is None:
        raise credenziali_non_valide
    if not utente.attivo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disattivato")
    return utente


CurrentUser = Annotated[Utente, Depends(get_current_user)]

# Da mettere in `dependencies=[...]` sulle rotte che richiedono il login ma non
# hanno bisogno dell'oggetto utente. La bacheca è riservata agli iscritti.
richiede_login = Depends(get_current_user)


def get_current_bagnino(utente: CurrentUser) -> ProfiloBagnino:
    """L'utente deve essere un bagnino e avere già creato il profilo."""
    if utente.tipo != TipoUtente.BAGNINO:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Riservato agli account bagnino")
    if utente.profilo_bagnino is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Devi prima creare il tuo profilo bagnino (POST /bagnini)"
        )
    return utente.profilo_bagnino


def get_current_piscina(utente: CurrentUser) -> ProfiloPiscina:
    """L'utente deve essere una struttura e avere già creato il profilo."""
    if utente.tipo != TipoUtente.PISCINA:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Riservato agli account piscina")
    if utente.profilo_piscina is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Devi prima creare il profilo della struttura (POST /piscine)"
        )
    return utente.profilo_piscina


CurrentBagnino = Annotated[ProfiloBagnino, Depends(get_current_bagnino)]
CurrentPiscina = Annotated[ProfiloPiscina, Depends(get_current_piscina)]
