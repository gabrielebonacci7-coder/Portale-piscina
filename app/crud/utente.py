"""Operazioni su account e credenziali."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.privacy import VERSIONE_INFORMATIVA
from app.core.security import hash_password, verify_password
from app.db.base_class import utcnow
from app.models import Utente
from app.schemas.auth import RegistrazioneRequest


def get_by_email(db: Session, email: str) -> Utente | None:
    # Le email si confrontano senza distinzione di maiuscole.
    return db.scalar(select(Utente).where(Utente.email == email.lower().strip()))


def crea_utente(db: Session, dati: RegistrazioneRequest) -> Utente:
    utente = Utente(
        email=dati.email.lower().strip(),
        telefono=dati.telefono,
        tipo=dati.tipo,
        telefono_pubblico=dati.telefono_pubblico,
        password_hash=hash_password(dati.password),
        # Si registra *quando* e *quale versione*: il consenso a un testo
        # vecchio non vale per uno riscritto.
        privacy_accettata_il=utcnow(),
        privacy_versione=VERSIONE_INFORMATIVA,
    )
    db.add(utente)
    db.commit()
    db.refresh(utente)
    return utente


def autentica(db: Session, email: str, password: str) -> Utente | None:
    """Restituisce l'utente se le credenziali sono corrette, altrimenti None."""
    utente = get_by_email(db, email)
    if utente is None:
        # Si verifica comunque un hash fittizio: senza questo, un'email
        # inesistente risponderebbe più in fretta di una esistente e si
        # potrebbe capire quali indirizzi sono registrati.
        verify_password(password, "$2b$12$" + "x" * 53)
        return None
    if not verify_password(password, utente.password_hash):
        return None
    return utente


def cambia_password(db: Session, utente: Utente, password_nuova: str) -> Utente:
    utente.password_hash = hash_password(password_nuova)
    db.commit()
    db.refresh(utente)
    return utente
