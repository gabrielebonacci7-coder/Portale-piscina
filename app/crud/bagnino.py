"""Operazioni sul profilo bagnino e sulle sue entità satellite."""

from datetime import date

from sqlalchemy import Select, exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Brevetto, Disponibilita, Esperienza, ProfiloBagnino, Zona
from app.models.zona import bagnino_zone
from app.schemas.bagnino import (
    BrevettoCreate,
    DisponibilitaCreate,
    EsperienzaCreate,
    ProfiloBagninoCreate,
    ProfiloBagninoUpdate,
)


def _carica_zone(db: Session, zone_ids: list[int]) -> list[Zona]:
    """Traduce una lista di id in oggetti Zona, ignorando i duplicati."""
    if not zone_ids:
        return []
    return list(db.scalars(select(Zona).where(Zona.id.in_(set(zone_ids)))))


def get(db: Session, bagnino_id: int) -> ProfiloBagnino | None:
    return db.get(ProfiloBagnino, bagnino_id)


def get_by_utente(db: Session, utente_id: int) -> ProfiloBagnino | None:
    return db.scalar(select(ProfiloBagnino).where(ProfiloBagnino.utente_id == utente_id))


def crea(db: Session, utente_id: int, dati: ProfiloBagninoCreate) -> ProfiloBagnino:
    campi = dati.model_dump(exclude={"zone_ids"})
    profilo = ProfiloBagnino(utente_id=utente_id, **campi)
    profilo.zone = _carica_zone(db, dati.zone_ids)
    db.add(profilo)
    db.commit()
    db.refresh(profilo)
    return profilo


def aggiorna(db: Session, profilo: ProfiloBagnino, dati: ProfiloBagninoUpdate) -> ProfiloBagnino:
    # `exclude_unset` distingue "campo assente" da "campo messo a null".
    campi = dati.model_dump(exclude_unset=True, exclude={"zone_ids"})
    for nome, valore in campi.items():
        setattr(profilo, nome, valore)
    if dati.zone_ids is not None:
        profilo.zone = _carica_zone(db, dati.zone_ids)
    db.commit()
    db.refresh(profilo)
    return profilo


def cerca(
    db: Session,
    *,
    citta: str | None = None,
    zona_id: int | None = None,
    solo_abilitati: bool = False,
    chiamata_singola: bool | None = None,
    anni_esperienza_min: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[int, list[ProfiloBagnino]]:
    """Ricerca bagnini per la bacheca. Restituisce (totale, risultati)."""
    filtri = [ProfiloBagnino.cerca_lavoro.is_(True)]

    if citta:
        filtri.append(ProfiloBagnino.citta == citta)
    if zona_id is not None:
        filtri.append(
            ProfiloBagnino.id.in_(
                select(bagnino_zone.c.bagnino_id).where(bagnino_zone.c.zona_id == zona_id)
            )
        )
    if chiamata_singola is not None:
        filtri.append(ProfiloBagnino.disponibile_chiamata_singola.is_(chiamata_singola))
    if anni_esperienza_min is not None:
        filtri.append(ProfiloBagnino.anni_esperienza >= anni_esperienza_min)
    if solo_abilitati:
        # Almeno un brevetto non ancora scaduto: il filtro sta nel database,
        # non in Python, così la paginazione resta corretta.
        filtri.append(
            exists().where(
                Brevetto.bagnino_id == ProfiloBagnino.id,
                Brevetto.data_scadenza.is_not(None),
                Brevetto.data_scadenza >= date.today(),
            )
        )

    base: Select = select(ProfiloBagnino).where(*filtri)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    risultati = db.scalars(
        base.options(selectinload(ProfiloBagnino.zone))
        .order_by(ProfiloBagnino.anni_esperienza.desc(), ProfiloBagnino.id)
        .offset(skip)
        .limit(limit)
    ).all()
    return totale, list(risultati)


# --- Entità satellite -----------------------------------------------------
def aggiungi_brevetto(db: Session, profilo: ProfiloBagnino, dati: BrevettoCreate) -> Brevetto:
    brevetto = Brevetto(bagnino_id=profilo.id, **dati.model_dump())
    db.add(brevetto)
    db.commit()
    db.refresh(brevetto)
    return brevetto


def aggiungi_esperienza(db: Session, profilo: ProfiloBagnino, dati: EsperienzaCreate) -> Esperienza:
    esperienza = Esperienza(bagnino_id=profilo.id, **dati.model_dump())
    db.add(esperienza)
    db.commit()
    db.refresh(esperienza)
    return esperienza


def aggiungi_disponibilita(
    db: Session, profilo: ProfiloBagnino, dati: DisponibilitaCreate
) -> Disponibilita:
    disponibilita = Disponibilita(bagnino_id=profilo.id, **dati.model_dump())
    db.add(disponibilita)
    db.commit()
    db.refresh(disponibilita)
    return disponibilita


def elimina_figlio(db: Session, modello, figlio_id: int, profilo: ProfiloBagnino) -> bool:
    """Cancella brevetto/esperienza/disponibilità solo se appartiene al profilo."""
    oggetto = db.get(modello, figlio_id)
    if oggetto is None or oggetto.bagnino_id != profilo.id:
        return False
    db.delete(oggetto)
    db.commit()
    return True
