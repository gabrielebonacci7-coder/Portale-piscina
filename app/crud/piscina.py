"""Operazioni sul profilo della struttura."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import ProfiloPiscina, TipoStruttura
from app.schemas.piscina import ProfiloPiscinaCreate, ProfiloPiscinaUpdate


def get(db: Session, piscina_id: int) -> ProfiloPiscina | None:
    return db.get(ProfiloPiscina, piscina_id)


def get_by_utente(db: Session, utente_id: int) -> ProfiloPiscina | None:
    return db.scalar(select(ProfiloPiscina).where(ProfiloPiscina.utente_id == utente_id))


def crea(db: Session, utente_id: int, dati: ProfiloPiscinaCreate) -> ProfiloPiscina:
    profilo = ProfiloPiscina(utente_id=utente_id, **dati.model_dump())
    db.add(profilo)
    db.commit()
    db.refresh(profilo)
    return profilo


def aggiorna(db: Session, profilo: ProfiloPiscina, dati: ProfiloPiscinaUpdate) -> ProfiloPiscina:
    for nome, valore in dati.model_dump(exclude_unset=True).items():
        setattr(profilo, nome, valore)
    db.commit()
    db.refresh(profilo)
    return profilo


def cerca(
    db: Session,
    *,
    citta: str | None = None,
    zona_id: int | None = None,
    tipo_struttura: TipoStruttura | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[int, list[ProfiloPiscina]]:
    filtri = [ProfiloPiscina.attiva.is_(True)]
    if citta:
        filtri.append(ProfiloPiscina.citta == citta)
    if zona_id is not None:
        filtri.append(ProfiloPiscina.zona_id == zona_id)
    if tipo_struttura is not None:
        filtri.append(ProfiloPiscina.tipo_struttura == tipo_struttura)

    base: Select = select(ProfiloPiscina).where(*filtri)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    risultati = db.scalars(
        base.options(selectinload(ProfiloPiscina.zona))
        .order_by(ProfiloPiscina.nome_struttura)
        .offset(skip)
        .limit(limit)
    ).all()
    return totale, list(risultati)
