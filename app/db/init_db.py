"""Creazione dello schema e anagrafica delle zone servite dalla bacheca."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine

# L'import di `app.models` registra tutte le tabelle su Base.metadata.
from app.models import Base, Zona

# Le zone sono raggruppate per "area": è così che si scelgono nell'app.
# (nome, città, sotto-etichetta)
ZONE: dict[str, list[tuple[str, str, str | None]]] = {
    # A Roma la zona è il quartiere e la sotto-etichetta è il municipio.
    "Roma": [
        ("Centro Storico", "Roma", "Municipio I"),
        ("Parioli / Flaminio", "Roma", "Municipio II"),
        ("Monte Sacro", "Roma", "Municipio III"),
        ("Tiburtina / Pietralata", "Roma", "Municipio IV"),
        ("Prenestino / Centocelle", "Roma", "Municipio V"),
        ("Torre Angela / Borghesiana", "Roma", "Municipio VI"),
        ("Appio / Tuscolano", "Roma", "Municipio VII"),
        ("Ostiense / Garbatella", "Roma", "Municipio VIII"),
        ("EUR", "Roma", "Municipio IX"),
        ("Ostia / Acilia", "Roma", "Municipio X"),
        ("Portuense / Marconi", "Roma", "Municipio XI"),
        ("Monteverde", "Roma", "Municipio XII"),
        ("Aurelio / Boccea", "Roma", "Municipio XIII"),
        ("Monte Mario", "Roma", "Municipio XIV"),
        ("Cassia / Flaminia", "Roma", "Municipio XV"),
    ],
    # Fuori Roma la zona è il comune: qui non ci sono municipi.
    # Ciampino e Velletri non sono Castelli in senso stretto, ma stanno nello
    # stesso bacino di spostamenti: chi lavora a Marino considera anche loro.
    "Castelli Romani": [
        ("Albano Laziale", "Albano Laziale", None),
        ("Ariccia", "Ariccia", None),
        ("Castel Gandolfo", "Castel Gandolfo", None),
        ("Ciampino", "Ciampino", None),
        ("Colonna", "Colonna", None),
        ("Frascati", "Frascati", None),
        ("Genzano di Roma", "Genzano di Roma", None),
        ("Grottaferrata", "Grottaferrata", None),
        ("Lanuvio", "Lanuvio", None),
        ("Marino", "Marino", None),
        ("Monte Compatri", "Monte Compatri", None),
        ("Monte Porzio Catone", "Monte Porzio Catone", None),
        ("Nemi", "Nemi", None),
        ("Rocca di Papa", "Rocca di Papa", None),
        ("Rocca Priora", "Rocca Priora", None),
        ("Velletri", "Velletri", None),
    ],
}

# Ordine in cui le aree compaiono nei menù: Roma per prima, è il grosso.
ORDINE_AREE = list(ZONE)


def create_tables() -> None:
    """Crea le tabelle mancanti. Non modifica quelle esistenti."""
    Base.metadata.create_all(bind=engine)


def seed_zone(db: Session) -> int:
    """Inserisce le zone non ancora presenti. Idempotente.

    Il confronto è su (città, nome), la stessa coppia del vincolo di unicità:
    così rilanciare il seed dopo aver aggiunto un'area inserisce solo le nuove.
    """
    esistenti = {(c, n) for c, n in db.execute(select(Zona.citta, Zona.nome))}
    nuove = [
        Zona(nome=nome, citta=citta, area=area, macro_area=macro)
        for area, elenco in ZONE.items()
        for nome, citta, macro in elenco
        if (citta, nome) not in esistenti
    ]
    db.add_all(nuove)
    db.commit()
    return len(nuove)


def init_db() -> None:
    create_tables()
    with SessionLocal() as db:
        aggiunte = seed_zone(db)
    totale = sum(len(v) for v in ZONE.values())
    print(f"Schema creato. Zone: {totale} in totale, {aggiunte} appena inserite.")


if __name__ == "__main__":
    init_db()
