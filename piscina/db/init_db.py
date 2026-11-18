"""Crea lo schema e mette in tabella le postazioni della piantina.

Si può rieseguire quante volte si vuole: aggiunge le postazioni nuove,
aggiorna le coordinate di quelle che già ci sono e non tocca `attiva`, che è
una decisione dello staff e non del file.

Toglie anche quelle sparite dalla piantina — altrimenti un ombrellone
cancellato resterebbe in tabella e la mappa continuerebbe a disegnarlo dove
non c'è più. Se però qualcuno ci ha già prenotato sopra, la postazione resta:
una prenotazione fatta non si cancella per un ritocco al disegno, e in quel
caso parte un avviso nel registro.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from piscina.db.session import SessionLocal, engine
from piscina.dominio.piantina import POSTAZIONI
from piscina.models import Base, Occupazione, Postazione

log = logging.getLogger("piscina.init")


def sincronizza_postazioni(db: Session) -> tuple[int, int, int]:
    """Allinea la tabella alla piantina.

    Restituisce (aggiunte, aggiornate, tolte)."""
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

    # Le postazioni che non stanno più sulla piantina.
    nella_piantina = {dati["codice"] for dati in POSTAZIONI}
    tolte = 0
    for codice, postazione in esistenti.items():
        if codice in nella_piantina:
            continue
        occupata = db.scalar(
            select(Occupazione.id).where(Occupazione.postazione_id == postazione.id).limit(1)
        )
        if occupata:
            log.warning(
                "La postazione %s non è più sulla piantina ma ha prenotazioni: la lascio.",
                codice,
            )
            continue
        db.delete(postazione)
        tolte += 1

    db.commit()
    return aggiunte, aggiornate, tolte


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        aggiunte, aggiornate, tolte = sincronizza_postazioni(db)
    if aggiunte or aggiornate or tolte:
        log.info(
            "Postazioni: %d aggiunte, %d aggiornate, %d tolte", aggiunte, aggiornate, tolte
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    init_db()
    print("Database pronto.")
