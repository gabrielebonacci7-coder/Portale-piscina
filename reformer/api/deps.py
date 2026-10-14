"""Dipendenze comuni ai router: chi sta chiamando, e la traduzione degli
errori delle regole in risposte HTTP."""

from contextlib import contextmanager

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from reformer.core.security import leggi_token
from reformer.db.session import get_db
from reformer.models import Utente
from reformer.servizi.regole import ErroreRegola

NON_AUTORIZZATO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sessione scaduta, accedi di nuovo",
    headers={"WWW-Authenticate": "Bearer"},
)


def utente_corrente(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> Utente:
    schema, _, token = authorization.partition(" ")
    if schema.lower() != "bearer" or not token:
        raise NON_AUTORIZZATO
    letto = leggi_token(token)
    if letto is None:
        raise NON_AUTORIZZATO
    utente_id, sessione = letto
    utente = db.get(Utente, utente_id)
    # Password cambiata o account cancellato: i token vecchi non valgono più.
    if utente is None or utente.cancellato_il is not None or utente.sessione != sessione:
        raise NON_AUTORIZZATO
    return utente


def solo_staff(utente: Utente = Depends(utente_corrente)) -> Utente:
    if not utente.e_staff:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Questa parte è riservata a Greta ed Elisa")
    return utente


@contextmanager
def regole():
    """`with regole(): ...` — un ErroreRegola diventa la risposta giusta."""
    try:
        yield
    except ErroreRegola as e:
        raise HTTPException(e.stato, e.messaggio) from e
