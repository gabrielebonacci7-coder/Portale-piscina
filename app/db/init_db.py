"""Creazione dello schema e seed delle zone di Roma."""

from sqlalchemy import select
from sqlalchemy.orm import Session

# L'import di `app.models` registra tutte le tabelle su Base.metadata.
from app.models import Base, Zona
from app.db.session import SessionLocal, engine

# Municipi di Roma: base minima per i filtri di zona della bacheca.
ZONE_ROMA: list[tuple[str, str]] = [
    ("Centro Storico", "Municipio I"),
    ("Parioli / Flaminio", "Municipio II"),
    ("Monte Sacro", "Municipio III"),
    ("Tiburtina / Pietralata", "Municipio IV"),
    ("Prenestino / Centocelle", "Municipio V"),
    ("Torre Angela / Borghesiana", "Municipio VI"),
    ("Appio / Tuscolano", "Municipio VII"),
    ("Ostiense / Garbatella", "Municipio VIII"),
    ("EUR", "Municipio IX"),
    ("Ostia / Acilia", "Municipio X"),
    ("Portuense / Marconi", "Municipio XI"),
    ("Monteverde", "Municipio XII"),
    ("Aurelio / Boccea", "Municipio XIII"),
    ("Monte Mario", "Municipio XIV"),
    ("Cassia / Flaminia", "Municipio XV"),
]


def create_tables() -> None:
    """Crea le tabelle mancanti. Non modifica quelle esistenti."""
    Base.metadata.create_all(bind=engine)


def seed_zone(db: Session) -> int:
    """Inserisce le zone di Roma non ancora presenti. Idempotente."""
    esistenti = set(db.scalars(select(Zona.nome).where(Zona.citta == "Roma")))
    nuove = [
        Zona(nome=nome, citta="Roma", macro_area=area)
        for nome, area in ZONE_ROMA
        if nome not in esistenti
    ]
    db.add_all(nuove)
    db.commit()
    return len(nuove)


def init_db() -> None:
    create_tables()
    with SessionLocal() as db:
        aggiunte = seed_zone(db)
    print(f"Schema creato. Zone inserite: {aggiunte}")


if __name__ == "__main__":
    init_db()
