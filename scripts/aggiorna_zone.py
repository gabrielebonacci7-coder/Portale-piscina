"""Aggiorna un database creato prima dell'aggiunta delle aree.

    python -m scripts.aggiorna_zone

`create_all` crea le tabelle mancanti ma non aggiunge colonne a quelle che
esistono già: un database creato prima di questa modifica non ha la colonna
`area` e l'app non parte. Questo script la aggiunge e la riempie.

È un rattoppo mirato, non un sistema di migrazioni: quando il progetto andrà
in produzione questo lavoro lo farà Alembic (vedi "Prossimi passi" nel README).
Chi parte da zero non ne ha bisogno: basta `python -m app.db.init_db`.
"""

from sqlalchemy import inspect, text

from app.db.init_db import seed_zone
from app.db.session import SessionLocal, engine


def colonne(tabella: str) -> set[str]:
    inspector = inspect(engine)
    if tabella not in inspector.get_table_names():
        return set()
    return {c["name"] for c in inspector.get_columns(tabella)}


def main() -> None:
    presenti = colonne("zone")
    if not presenti:
        print("Nessuna tabella `zone`: usa `python -m app.db.init_db`.")
        return

    if "area" in presenti:
        print("La colonna `area` c'è già.")
    else:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE zone ADD COLUMN area VARCHAR(80)"))
            # Le zone già presenti sono tutte romane: è l'unica area che
            # esisteva prima di questa modifica.
            conn.execute(text("UPDATE zone SET area = 'Roma' WHERE area IS NULL"))
        print("Colonna `area` aggiunta, zone esistenti assegnate a Roma.")

    with SessionLocal() as db:
        aggiunte = seed_zone(db)
    print(f"Zone nuove inserite: {aggiunte}")


if __name__ == "__main__":
    main()
