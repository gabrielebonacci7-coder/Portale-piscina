"""Chat interna: trova/crea conversazioni, invia messaggi, conta i non letti."""

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Blocco, Conversazione, Messaggio, Partecipante, Utente
from app.schemas.messaggistica import MessaggioCreate


def get_conversazione(db: Session, conversazione_id: int) -> Conversazione | None:
    return db.get(Conversazione, conversazione_id)


def partecipa(conversazione: Conversazione, utente_id: int) -> bool:
    return any(p.utente_id == utente_id for p in conversazione.partecipanti)


# --- Blocchi --------------------------------------------------------------
def blocco_fra(db: Session, a_id: int, b_id: int) -> Blocco | None:
    """Un blocco in una direzione qualsiasi impedisce lo scambio in entrambe.

    Chi blocca non vuole essere contattato; chi è bloccato non deve poter
    aggirare la cosa scrivendo per primo.
    """
    return db.scalar(
        select(Blocco).where(
            or_(
                (Blocco.bloccante_id == a_id) & (Blocco.bloccato_id == b_id),
                (Blocco.bloccante_id == b_id) & (Blocco.bloccato_id == a_id),
            )
        )
    )


def blocca(db: Session, bloccante: Utente, bloccato_id: int, motivo: str | None) -> Blocco:
    esistente = db.scalar(
        select(Blocco).where(
            Blocco.bloccante_id == bloccante.id, Blocco.bloccato_id == bloccato_id
        )
    )
    if esistente is not None:
        return esistente
    blocco = Blocco(bloccante_id=bloccante.id, bloccato_id=bloccato_id, motivo=motivo)
    db.add(blocco)
    db.commit()
    db.refresh(blocco)
    return blocco


def sblocca(db: Session, bloccante_id: int, bloccato_id: int) -> bool:
    blocco = db.scalar(
        select(Blocco).where(
            Blocco.bloccante_id == bloccante_id, Blocco.bloccato_id == bloccato_id
        )
    )
    if blocco is None:
        return False
    db.delete(blocco)
    db.commit()
    return True


def elenco_blocchi(db: Session, utente_id: int) -> list[Blocco]:
    return list(
        db.scalars(
            select(Blocco).where(Blocco.bloccante_id == utente_id).order_by(Blocco.creato_il.desc())
        )
    )


# --- Conversazioni --------------------------------------------------------
def trova_diretta(db: Session, a_id: int, b_id: int) -> Conversazione | None:
    """La conversazione a due fra questi utenti, se già esiste.

    Si cercano le conversazioni in cui compare `a`, che hanno esattamente due
    partecipanti e fra questi c'è `b`.
    """
    conv_di_a = select(Partecipante.conversazione_id).where(Partecipante.utente_id == a_id)
    conv_di_b = select(Partecipante.conversazione_id).where(Partecipante.utente_id == b_id)
    solo_due = (
        select(Partecipante.conversazione_id)
        .group_by(Partecipante.conversazione_id)
        .having(func.count(Partecipante.id) == 2)
    )
    return db.scalar(
        select(Conversazione)
        .where(
            Conversazione.id.in_(conv_di_a),
            Conversazione.id.in_(conv_di_b),
            Conversazione.id.in_(solo_due),
        )
        .limit(1)
    )


def crea_diretta(
    db: Session, a_id: int, b_id: int, annuncio_id: int | None = None
) -> Conversazione:
    conversazione = Conversazione(annuncio_id=annuncio_id)
    conversazione.partecipanti = [
        Partecipante(utente_id=a_id),
        Partecipante(utente_id=b_id),
    ]
    db.add(conversazione)
    db.commit()
    db.refresh(conversazione)
    return conversazione


def trova_o_crea_diretta(
    db: Session, a_id: int, b_id: int, annuncio_id: int | None = None
) -> Conversazione:
    """Fra due persone la conversazione resta una sola, anche cambiando annuncio."""
    esistente = trova_diretta(db, a_id, b_id)
    return esistente if esistente is not None else crea_diretta(db, a_id, b_id, annuncio_id)


def invia(db: Session, conversazione: Conversazione, mittente: Utente, dati: MessaggioCreate):
    adesso = datetime.now(timezone.utc)
    messaggio = Messaggio(
        conversazione_id=conversazione.id,
        mittente_id=mittente.id,
        testo=dati.testo,
        creato_il=adesso,
    )
    db.add(messaggio)
    # Denormalizzato apposta: ordinare l'elenco delle conversazioni senza
    # toccare la tabella dei messaggi a ogni caricamento.
    conversazione.ultimo_messaggio_il = adesso
    # Chi scrive ha per definizione letto tutto fino a quel punto.
    for p in conversazione.partecipanti:
        if p.utente_id == mittente.id:
            p.ultimo_letto_il = adesso
    db.commit()
    db.refresh(messaggio)
    return messaggio


def conta_non_letti(db: Session, conversazione_id: int, utente_id: int) -> int:
    """Messaggi altrui arrivati dopo l'ultima lettura."""
    partecipante = db.scalar(
        select(Partecipante).where(
            Partecipante.conversazione_id == conversazione_id,
            Partecipante.utente_id == utente_id,
        )
    )
    if partecipante is None:
        return 0
    filtri = [
        Messaggio.conversazione_id == conversazione_id,
        Messaggio.mittente_id != utente_id,
    ]
    if partecipante.ultimo_letto_il is not None:
        filtri.append(Messaggio.creato_il > partecipante.ultimo_letto_il)
    return db.scalar(select(func.count()).select_from(Messaggio).where(*filtri)) or 0


def segna_letta(db: Session, conversazione_id: int, utente_id: int) -> None:
    partecipante = db.scalar(
        select(Partecipante).where(
            Partecipante.conversazione_id == conversazione_id,
            Partecipante.utente_id == utente_id,
        )
    )
    if partecipante is not None:
        partecipante.ultimo_letto_il = datetime.now(timezone.utc)
        db.commit()


def ultimo_testo(db: Session, conversazione_id: int) -> str | None:
    return db.scalar(
        select(Messaggio.testo)
        .where(Messaggio.conversazione_id == conversazione_id)
        .order_by(Messaggio.creato_il.desc())
        .limit(1)
    )


def elenco_conversazioni(
    db: Session, utente_id: int, *, skip: int = 0, limit: int = 30
) -> tuple[int, list[Conversazione]]:
    mie = select(Partecipante.conversazione_id).where(Partecipante.utente_id == utente_id)
    base = select(Conversazione).where(Conversazione.id.in_(mie))
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    risultati = db.scalars(
        base.options(
            selectinload(Conversazione.partecipanti)
            .selectinload(Partecipante.utente)
            .selectinload(Utente.profilo_bagnino),
            selectinload(Conversazione.partecipanti)
            .selectinload(Partecipante.utente)
            .selectinload(Utente.profilo_piscina),
        )
        # Le conversazioni senza messaggi finiscono in fondo, non in cima.
        .order_by(Conversazione.ultimo_messaggio_il.desc().nullslast())
        .offset(skip)
        .limit(limit)
    ).all()
    return totale, list(risultati)


def messaggi(
    db: Session, conversazione_id: int, *, skip: int = 0, limit: int = 50
) -> tuple[int, list[Messaggio]]:
    base = select(Messaggio).where(Messaggio.conversazione_id == conversazione_id)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    risultati = db.scalars(
        base.order_by(Messaggio.creato_il).offset(skip).limit(limit)
    ).all()
    return totale, list(risultati)
