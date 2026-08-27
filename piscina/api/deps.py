"""Dipendenze comuni ai router: chi sta chiamando."""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from piscina.core.security import leggi_token
from piscina.db.session import get_db
from piscina.models import Operatore

NON_AUTORIZZATO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sessione scaduta, accedi di nuovo",
    headers={"WWW-Authenticate": "Bearer"},
)


def operatore_corrente(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> Operatore:
    """L'operatore dello staff che ha fatto la richiesta, o 401."""
    if not authorization.lower().startswith("bearer "):
        raise NON_AUTORIZZATO
    operatore_id = leggi_token(authorization.split(" ", 1)[1].strip())
    if operatore_id is None:
        raise NON_AUTORIZZATO
    operatore = db.get(Operatore, operatore_id)
    if operatore is None or not operatore.attivo:
        raise NON_AUTORIZZATO
    return operatore
