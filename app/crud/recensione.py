"""Operazioni sulle recensioni, con le regole su chi può recensire chi."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Annuncio, Recensione, StatoAnnuncio, TipoUtente, Utente
from app.schemas.recensione import RecensioneCreate

# Stati in cui il turno si considera avvenuto: prima non si recensisce.
STATI_RECENSIBILI = {StatoAnnuncio.ASSEGNATO, StatoAnnuncio.CHIUSO}

# Voti di dettaglio ammessi per ciascun verso.
VOTI_AMMESSI: dict[TipoUtente, set[str]] = {
    # La struttura giudica il bagnino.
    TipoUtente.PISCINA: {"voto_puntualita", "voto_professionalita"},
    # Il bagnino giudica la struttura.
    TipoUtente.BAGNINO: {"voto_ambiente", "voto_pagamento"},
}


def get(db: Session, recensione_id: int) -> Recensione | None:
    return db.get(Recensione, recensione_id)


def hanno_lavorato_insieme(annuncio: Annuncio, autore_id: int, destinatario_id: int) -> bool:
    """I due devono essere le due parti dello stesso annuncio, in un verso o nell'altro."""
    if annuncio.assegnato_a_id is None:
        return False
    parti = {annuncio.autore_id, annuncio.assegnato_a_id}
    return parti == {autore_id, destinatario_id}


def voti_fuori_posto(dati: RecensioneCreate, autore: Utente) -> list[str]:
    """Elenca i voti di dettaglio che non hanno senso nel verso di questa recensione."""
    ammessi = VOTI_AMMESSI[autore.tipo]
    tutti = {"voto_puntualita", "voto_professionalita", "voto_ambiente", "voto_pagamento"}
    return sorted(
        campo
        for campo in tutti - ammessi
        if getattr(dati, campo) is not None
    )


def esiste_gia(db: Session, autore_id: int, destinatario_id: int, annuncio_id: int | None) -> bool:
    return db.scalar(
        select(func.count())
        .select_from(Recensione)
        .where(
            Recensione.autore_id == autore_id,
            Recensione.destinatario_id == destinatario_id,
            Recensione.annuncio_id == annuncio_id,
        )
    ) not in (0, None)


def crea(db: Session, autore: Utente, dati: RecensioneCreate) -> Recensione:
    recensione = Recensione(autore_id=autore.id, **dati.model_dump())
    db.add(recensione)
    db.commit()
    db.refresh(recensione)
    return recensione


def elenco_per_destinatario(
    db: Session, destinatario_id: int, *, skip: int = 0, limit: int = 20
) -> tuple[int, list[Recensione]]:
    base = select(Recensione).where(Recensione.destinatario_id == destinatario_id)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    risultati = db.scalars(
        base.options(
            selectinload(Recensione.autore).selectinload(Utente.profilo_bagnino),
            selectinload(Recensione.autore).selectinload(Utente.profilo_piscina),
        )
        .order_by(Recensione.creato_il.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return totale, list(risultati)


def medie(db: Session, destinatario_id: int) -> dict[str, float | None]:
    """Medie dei voti, calcolate dal database su tutte le recensioni ricevute."""
    riga = db.execute(
        select(
            func.avg(Recensione.stelle),
            func.avg(Recensione.voto_puntualita),
            func.avg(Recensione.voto_professionalita),
            func.avg(Recensione.voto_ambiente),
            func.avg(Recensione.voto_pagamento),
        ).where(Recensione.destinatario_id == destinatario_id)
    ).one()

    def arrotonda(valore) -> float | None:
        return round(float(valore), 2) if valore is not None else None

    return {
        "media_stelle": arrotonda(riga[0]),
        "media_puntualita": arrotonda(riga[1]),
        "media_professionalita": arrotonda(riga[2]),
        "media_ambiente": arrotonda(riga[3]),
        "media_pagamento": arrotonda(riga[4]),
    }
