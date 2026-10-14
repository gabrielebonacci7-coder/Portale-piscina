"""Copia di sicurezza del database.

    python -m reformer.scripts.backup                    # in ./backup
    python -m reformer.scripts.backup --dove /dati/backup
    python -m reformer.scripts.backup --tieni 30         # quante copie conservare

Sul server: `docker compose exec app python -m reformer.scripts.backup --dove /dati/backup`
(vedi MESSA-ONLINE.md per farlo partire da solo ogni notte).

**Il database non si copia con `cp`.** Se qualcuno sta prenotando mentre
copi, il file può essere a metà di una scrittura: sembra a posto ma i dati
dentro non tornano. Qui si usa l'API di backup di SQLite, che fa una copia
coerente anche con l'app accesa.
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from reformer.core.config import settings


def main() -> int:
    p = argparse.ArgumentParser(description="Copia di sicurezza del database")
    p.add_argument("--dove", default="backup", help="cartella delle copie")
    p.add_argument("--tieni", type=int, default=30, help="quante copie conservare")
    a = p.parse_args()

    url = settings.database_url
    if not url.startswith("sqlite"):
        print("Database non SQLite: usa lo strumento del tuo database (pg_dump...)")
        return 1
    origine = Path(url.split("///")[-1])
    if not origine.exists():
        print(f"Database non trovato in {origine}")
        return 1

    cartella = Path(a.dove)
    cartella.mkdir(parents=True, exist_ok=True)
    destinazione = cartella / f"reformer-{datetime.now():%Y-%m-%d-%H%M}.db"
    with sqlite3.connect(f"file:{origine}?mode=ro", uri=True) as sorgente, sqlite3.connect(destinazione) as copia:
        sorgente.backup(copia)
    print(f"Copia fatta: {destinazione} ({destinazione.stat().st_size // 1024} kB)")

    copie = sorted(cartella.glob("reformer-*.db"), reverse=True)
    for vecchia in copie[a.tieni:]:
        vecchia.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
