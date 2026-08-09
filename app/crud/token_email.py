"""Token monouso per verifica indirizzo e recupero password."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import TipoToken, TokenEmail, Utente

# Quanto vale un token, per tipo.
DURATA = {
    TipoToken.RECUPERO_PASSWORD: lambda: timedelta(minutes=settings.minuti_validita_recupero),
    TipoToken.VERIFICA_EMAIL: lambda: timedelta(hours=settings.ore_validita_verifica),
}


def impronta(codice: str) -> str:
    """SHA-256 del codice: è quello che finisce nel database."""
    return hashlib.sha256(codice.encode("utf-8")).hexdigest()


def crea(db: Session, utente: Utente, tipo: TipoToken) -> str:
    """Genera un token e restituisce il codice **in chiaro**, una volta sola.

    Nel database resta solo l'impronta: dopo questa chiamata il codice non è
    più recuperabile da nessuna parte, esattamente come dev'essere.
    """
    # I token vecchi dello stesso tipo si annullano: chiedere un nuovo link
    # deve invalidare il precedente, altrimenti restano in giro più chiavi
    # buone per lo stesso account.
    annulla_precedenti(db, utente.id, tipo)

    codice = secrets.token_urlsafe(32)
    db.add(
        TokenEmail(
            utente_id=utente.id,
            tipo=tipo,
            impronta=impronta(codice),
            scade_il=datetime.now(timezone.utc) + DURATA[tipo](),
        )
    )
    db.commit()
    return codice


def annulla_precedenti(db: Session, utente_id: int, tipo: TipoToken) -> int:
    adesso = datetime.now(timezone.utc)
    quanti = (
        db.query(TokenEmail)
        .filter(
            TokenEmail.utente_id == utente_id,
            TokenEmail.tipo == tipo,
            TokenEmail.usato_il.is_(None),
        )
        .update({TokenEmail.usato_il: adesso}, synchronize_session=False)
    )
    db.commit()
    return quanti


def trova_valido(db: Session, codice: str, tipo: TipoToken) -> TokenEmail | None:
    """Il token corrispondente al codice, se esiste ed è ancora buono."""
    token = db.scalar(
        select(TokenEmail).where(
            TokenEmail.impronta == impronta(codice), TokenEmail.tipo == tipo
        )
    )
    return token if token is not None and token.valido else None


def _consuma(db: Session, token: TokenEmail) -> None:
    token.usato_il = datetime.now(timezone.utc)


def verifica_email(db: Session, token: TokenEmail) -> Utente:
    utente = token.utente
    utente.email_verificata = True
    _consuma(db, token)
    db.commit()
    db.refresh(utente)
    return utente


def reimposta_password(db: Session, token: TokenEmail, password_nuova: str) -> Utente:
    utente = token.utente
    utente.password_hash = hash_password(password_nuova)
    # Chi reimposta la password ha dimostrato di leggere quella casella:
    # tanto vale considerare l'indirizzo confermato.
    utente.email_verificata = True
    _consuma(db, token)
    db.commit()
    db.refresh(utente)
    return utente


def link(azione: str, codice: str) -> str:
    """Il link da mettere nell'email.

    Punta alla radice con un parametro, non a un percorso tipo
    `/recupero-password`: l'app è una pagina sola, e un percorso diverso
    darebbe 404 prima ancora che il codice venga letto.
    """
    return f"{settings.url_pubblico.rstrip('/')}/?{azione}={codice}"
