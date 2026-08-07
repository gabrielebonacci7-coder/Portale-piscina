"""Candidature: regole su chi può candidarsi e cosa succede quando si accetta."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Annuncio,
    Candidatura,
    StatoAnnuncio,
    StatoCandidatura,
    TipoUtente,
    Utente,
    brevetto_copre,
)
from app.models.enums import TipoAnnuncio
from app.schemas.candidatura import CandidaturaCreate

# A ogni tipo di annuncio risponde il tipo di account opposto a chi l'ha scritto.
CANDIDATO_ATTESO: dict[TipoAnnuncio, TipoUtente] = {
    TipoAnnuncio.PISCINA_CERCA_BAGNINO: TipoUtente.BAGNINO,
    TipoAnnuncio.BAGNINO_CERCA_SOSTITUZIONE: TipoUtente.PISCINA,
}


def get(db: Session, candidatura_id: int) -> Candidatura | None:
    return db.get(Candidatura, candidatura_id)


def tipo_candidato_corretto(annuncio: Annuncio, candidato: Utente) -> bool:
    """A "piscina cerca bagnino" rispondono i bagnini, e viceversa."""
    return CANDIDATO_ATTESO[annuncio.tipo] == candidato.tipo


def annuncio_aperto(annuncio: Annuncio) -> bool:
    """Ci si candida solo a turni ancora aperti e non ancora iniziati."""
    return annuncio.stato == StatoAnnuncio.APERTO and annuncio.data_inizio >= datetime.now(
        timezone.utc
    )


def brevetto_sufficiente(annuncio: Annuncio, candidato: Utente) -> bool:
    """Verifica il brevetto richiesto dall'annuncio, tenendo conto della gerarchia.

    Vale solo per i bagnini: una struttura non ha brevetti da esibire.
    """
    if annuncio.brevetto_richiesto is None:
        return True
    if candidato.tipo != TipoUtente.BAGNINO:
        return True
    profilo = candidato.profilo_bagnino
    if profilo is None:
        return False
    # Solo i brevetti non scaduti contano.
    return any(
        brevetto_copre(b.tipo, annuncio.brevetto_richiesto) for b in profilo.brevetti_validi
    )


def gia_candidato(db: Session, annuncio_id: int, candidato_id: int) -> Candidatura | None:
    return db.scalar(
        select(Candidatura).where(
            Candidatura.annuncio_id == annuncio_id,
            Candidatura.candidato_id == candidato_id,
        )
    )


def crea(
    db: Session, annuncio: Annuncio, candidato: Utente, dati: CandidaturaCreate
) -> Candidatura:
    candidatura = Candidatura(
        annuncio_id=annuncio.id, candidato_id=candidato.id, messaggio=dati.messaggio
    )
    db.add(candidatura)
    db.commit()
    db.refresh(candidatura)
    return candidatura


def ritira(db: Session, candidatura: Candidatura) -> Candidatura:
    candidatura.stato = StatoCandidatura.RITIRATA
    db.commit()
    db.refresh(candidatura)
    return candidatura


def accetta(db: Session, candidatura: Candidatura) -> Candidatura:
    """Accetta la candidatura, assegna il turno e rifiuta le altre in attesa.

    Le tre cose stanno in un'unica transazione: un turno assegnato senza
    candidatura accettata (o viceversa) sarebbe uno stato incoerente.
    """
    annuncio = candidatura.annuncio

    candidatura.stato = StatoCandidatura.ACCETTATA
    annuncio.assegnato_a_id = candidatura.candidato_id
    annuncio.stato = StatoAnnuncio.ASSEGNATO

    db.query(Candidatura).filter(
        Candidatura.annuncio_id == annuncio.id,
        Candidatura.id != candidatura.id,
        Candidatura.stato == StatoCandidatura.INVIATA,
    ).update({Candidatura.stato: StatoCandidatura.RIFIUTATA}, synchronize_session=False)

    db.commit()
    db.refresh(candidatura)
    return candidatura


def rifiuta(db: Session, candidatura: Candidatura) -> Candidatura:
    candidatura.stato = StatoCandidatura.RIFIUTATA
    db.commit()
    db.refresh(candidatura)
    return candidatura


def _con_candidato(query):
    """Carica in anticipo il candidato e il suo profilo, per il nome mostrato."""
    return query.options(
        selectinload(Candidatura.candidato).selectinload(Utente.profilo_bagnino),
        selectinload(Candidatura.candidato).selectinload(Utente.profilo_piscina),
    )


def per_annuncio(
    db: Session, annuncio_id: int, *, skip: int = 0, limit: int = 50
) -> tuple[int, list[Candidatura]]:
    base = select(Candidatura).where(Candidatura.annuncio_id == annuncio_id)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    risultati = db.scalars(
        _con_candidato(base).order_by(Candidatura.creato_il).offset(skip).limit(limit)
    ).all()
    return totale, list(risultati)


def per_candidato(
    db: Session, candidato_id: int, *, skip: int = 0, limit: int = 50
) -> tuple[int, list[Candidatura]]:
    base = select(Candidatura).where(Candidatura.candidato_id == candidato_id)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    risultati = db.scalars(
        _con_candidato(base)
        .options(selectinload(Candidatura.annuncio))
        .order_by(Candidatura.creato_il.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return totale, list(risultati)
