"""Operazioni sugli annunci: creazione, ricerca in bacheca, assegnazione."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Annuncio,
    StatoAnnuncio,
    TipoAnnuncio,
    TipoBrevetto,
    TipoTurno,
    TipoUtente,
    Utente,
)
from app.schemas.annuncio import AnnuncioCreate, AnnuncioUpdate

# Ogni tipo di annuncio può essere pubblicato solo dal tipo di account giusto.
AUTORE_ATTESO: dict[TipoAnnuncio, TipoUtente] = {
    TipoAnnuncio.PISCINA_CERCA_BAGNINO: TipoUtente.PISCINA,
    TipoAnnuncio.BAGNINO_CERCA_SOSTITUZIONE: TipoUtente.BAGNINO,
}


def tipo_coerente_con_autore(tipo: TipoAnnuncio, autore: Utente) -> bool:
    """Una piscina non può pubblicare "bagnino cerca sostituzione", e viceversa."""
    return AUTORE_ATTESO[tipo] == autore.tipo


def get(db: Session, annuncio_id: int) -> Annuncio | None:
    return db.get(Annuncio, annuncio_id)


def crea(db: Session, autore: Utente, dati: AnnuncioCreate) -> Annuncio:
    campi = dati.model_dump()
    # Se pubblica una struttura e non ha indicato la piscina, si usa la sua.
    if campi.get("piscina_id") is None and autore.profilo_piscina is not None:
        campi["piscina_id"] = autore.profilo_piscina.id

    annuncio = Annuncio(autore_id=autore.id, **campi)
    db.add(annuncio)
    db.commit()
    db.refresh(annuncio)
    return annuncio


def aggiorna(db: Session, annuncio: Annuncio, dati: AnnuncioUpdate) -> Annuncio:
    for nome, valore in dati.model_dump(exclude_unset=True).items():
        setattr(annuncio, nome, valore)
    db.commit()
    db.refresh(annuncio)
    return annuncio


def elimina(db: Session, annuncio: Annuncio) -> None:
    db.delete(annuncio)
    db.commit()


def assegna(db: Session, annuncio: Annuncio, destinatario: Utente) -> Annuncio:
    """Chiude il cerchio: il turno è coperto da `destinatario`."""
    annuncio.assegnato_a_id = destinatario.id
    annuncio.stato = StatoAnnuncio.ASSEGNATO
    db.commit()
    db.refresh(annuncio)
    return annuncio


def cerca(
    db: Session,
    *,
    tipo: TipoAnnuncio | None = None,
    citta: str | None = None,
    zona_id: int | None = None,
    tipo_turno: TipoTurno | None = None,
    brevetto_richiesto: TipoBrevetto | None = None,
    solo_urgenti: bool = False,
    solo_aperti: bool = True,
    data_da: datetime | None = None,
    data_a: datetime | None = None,
    compenso_min: Decimal | None = None,
    testo: str | None = None,
    autore_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[int, list[Annuncio]]:
    """Ricerca in bacheca. Restituisce (totale, risultati)."""
    filtri = []

    if solo_aperti:
        # "Aperto" significa sia stato aperto sia turno non ancora iniziato.
        filtri.append(Annuncio.stato == StatoAnnuncio.APERTO)
        filtri.append(Annuncio.data_inizio >= datetime.now(timezone.utc))
    if tipo is not None:
        filtri.append(Annuncio.tipo == tipo)
    if citta:
        filtri.append(Annuncio.citta == citta)
    if zona_id is not None:
        filtri.append(Annuncio.zona_id == zona_id)
    if tipo_turno is not None:
        filtri.append(Annuncio.tipo_turno == tipo_turno)
    if brevetto_richiesto is not None:
        # Vanno bene anche gli annunci che non chiedono un brevetto specifico.
        filtri.append(
            or_(
                Annuncio.brevetto_richiesto == brevetto_richiesto,
                Annuncio.brevetto_richiesto.is_(None),
            )
        )
    if solo_urgenti:
        filtri.append(Annuncio.urgente.is_(True))
    if data_da is not None:
        filtri.append(Annuncio.data_inizio >= data_da)
    if data_a is not None:
        filtri.append(Annuncio.data_inizio <= data_a)
    if compenso_min is not None:
        filtri.append(Annuncio.compenso >= compenso_min)
    if autore_id is not None:
        filtri.append(Annuncio.autore_id == autore_id)
    if testo:
        like = f"%{testo.strip()}%"
        filtri.append(or_(Annuncio.titolo.ilike(like), Annuncio.note.ilike(like)))

    base: Select = select(Annuncio).where(*filtri)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    risultati = db.scalars(
        base.options(
            selectinload(Annuncio.zona),
            # L'autore serve per il nome mostrato in scheda: caricarlo qui
            # evita una query per ogni annuncio della pagina.
            selectinload(Annuncio.autore).selectinload(Utente.profilo_bagnino),
            selectinload(Annuncio.autore).selectinload(Utente.profilo_piscina),
        )
        # Prima gli urgenti, poi i turni più vicini nel tempo.
        .order_by(Annuncio.urgente.desc(), Annuncio.data_inizio)
        .offset(skip)
        .limit(limit)
    ).all()
    return totale, list(risultati)


def segna_scaduti(db: Session) -> int:
    """Porta a SCADUTO gli annunci aperti il cui turno è ormai passato."""
    aggiornati = (
        db.query(Annuncio)
        .filter(
            Annuncio.stato == StatoAnnuncio.APERTO,
            Annuncio.data_inizio < datetime.now(timezone.utc),
        )
        .update({Annuncio.stato: StatoAnnuncio.SCADUTO}, synchronize_session=False)
    )
    db.commit()
    return aggiornati
