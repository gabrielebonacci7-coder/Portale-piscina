"""Crea lo schema e mette in tabella le postazioni della piantina.

Si può rieseguire quante volte si vuole: aggiunge le postazioni nuove,
aggiorna le coordinate di quelle che già ci sono e non tocca `attiva`, che è
una decisione dello staff e non del file.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from piscina.db.session import SessionLocal, engine
from piscina.dominio.piantina import POSTAZIONI
from piscina.models import Base, Postazione

log = logging.getLogger("piscina.init")


def sincronizza_postazioni(db: Session) -> tuple[int, int]:
    """Allinea la tabella alla piantina. Restituisce (aggiunte, aggiornate)."""
    esistenti = {p.codice: p for p in db.scalars(select(Postazione))}
    aggiunte = aggiornate = 0

    for dati in POSTAZIONI:
        postazione = esistenti.get(dati["codice"])
        if postazione is None:
            db.add(Postazione(**dati))
            aggiunte += 1
            continue
        cambiata = False
        for campo in ("tipo", "fila", "x", "y", "max_lettini"):
            if getattr(postazione, campo) != dati[campo]:
                setattr(postazione, campo, dati[campo])
                cambiata = True
        aggiornate += cambiata

    db.commit()
    return aggiunte, aggiornate


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        aggiunte, aggiornate = sincronizza_postazioni(db)
    if aggiunte or aggiornate:
        log.info("Postazioni: %d aggiunte, %d aggiornate", aggiunte, aggiornate)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    init_db()
    print("Database pronto.")
