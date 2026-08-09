"""Aggiorna un database creato con una versione precedente.

    python -m scripts.aggiorna_schema

`create_all` crea le tabelle mancanti ma **non aggiunge colonne** a quelle che
esistono già: un database vecchio resta senza i campi nuovi e l'app non parte.
Questo script aggiunge le colonne mancanti e le riempie con un valore sensato.

È un rattoppo mirato, non un sistema di migrazioni: quando il progetto andrà
in produzione questo lavoro lo farà Alembic (vedi "Prossimi passi" nel README).
Chi parte da zero non ne ha bisogno: basta `python -m app.db.init_db`.
"""

from sqlalchemy import inspect, text

from app.db.init_db import ZONE, create_tables, seed_zone
from app.db.session import SessionLocal, engine

# (tabella, colonna, definizione SQL, valore per le righe già presenti)
COLONNE_AGGIUNTE = [
    ("zone", "area", "VARCHAR(80)", None),
    ("utenti", "email_verificata", "BOOLEAN", "0"),
    ("profili_bagnino", "foto", "VARCHAR(255)", None),
]


def colonne(tabella: str) -> set[str]:
    inspector = inspect(engine)
    if tabella not in inspector.get_table_names():
        return set()
    return {c["name"] for c in inspector.get_columns(tabella)}


def riempi_aree() -> None:
    """Assegna l'area alle zone che già c'erano.

    Si ricava dall'anagrafica in `init_db`, invece di mettere "Roma" a tutte:
    un database che aveva già i Castelli se li vedrebbe spostati a Roma.
    """
    with engine.begin() as conn:
        for area, elenco in ZONE.items():
            for nome, citta, _ in elenco:
                conn.execute(
                    text("UPDATE zone SET area = :a WHERE citta = :c AND nome = :n"),
                    {"a": area, "c": citta, "n": nome},
                )
        # Zone aggiunte a mano, che l'anagrafica non conosce.
        rimaste = conn.execute(
            text("UPDATE zone SET area = 'Roma' WHERE area IS NULL")
        ).rowcount
    if rimaste:
        print(f"    ({rimaste} zone non in anagrafica assegnate a Roma)")


def main() -> None:
    if not colonne("utenti"):
        print("Database vuoto: usa `python -m app.db.init_db`.")
        return

    # Le tabelle nuove le crea create_all senza problemi: mancano solo le
    # colonne aggiunte a tabelle preesistenti.
    create_tables()

    for tabella, colonna, tipo, valore in COLONNE_AGGIUNTE:
        presenti = colonne(tabella)
        if not presenti:
            continue
        if colonna in presenti:
            print(f"  {tabella}.{colonna}: già presente")
            continue
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {tabella} ADD COLUMN {colonna} {tipo}"))
            if valore is not None:
                conn.execute(
                    text(f"UPDATE {tabella} SET {colonna} = {valore} WHERE {colonna} IS NULL")
                )
        print(f"  {tabella}.{colonna}: aggiunta")
        if (tabella, colonna) == ("zone", "area"):
            riempi_aree()

    with SessionLocal() as db:
        aggiunte = seed_zone(db)
    print(f"Zone nuove inserite: {aggiunte}")


if __name__ == "__main__":
    main()
