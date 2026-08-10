"""Copia di sicurezza del database e delle foto.

    python -m scripts.backup                    # in ./backup
    python -m scripts.backup --dove /mnt/dati   # altrove
    python -m scripts.backup --tieni 30         # quante copie conservare

Su un VPS il backup è responsabilità di chi lo affitta: nessuno lo fa al posto
tuo, e se il disco si rompe non c'è nessun "annulla".

**Il database non si copia con `cp`.** Se qualcuno sta scrivendo mentre copi,
il file che ottieni può essere a metà di una transazione: sembra a posto e si
apre, ma i dati dentro non tornano. Qui si usa l'API di backup di SQLite, che
produce una copia coerente anche con l'applicazione accesa.
"""

import argparse
import shutil
import sqlite3
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def percorso_sqlite() -> Path | None:
    """Il file del database, se si sta usando SQLite."""
    url = settings.database_url
    if not url.startswith("sqlite"):
        return None
    return Path(url.split("///")[-1])


def salva_database(destinazione: Path) -> Path | None:
    origine = percorso_sqlite()
    if origine is None:
        print("Database non SQLite: usa lo strumento di backup del tuo server")
        print("  (per PostgreSQL:  pg_dump ...)")
        return None
    if not origine.exists():
        print(f"Database non trovato in {origine}")
        return None

    with sqlite3.connect(f"file:{origine}?mode=ro", uri=True) as sorgente:
        with sqlite3.connect(destinazione) as copia:
            # Copia coerente anche mentre l'app scrive: è tutto il punto.
            sorgente.backup(copia)
    return destinazione


def salva_foto(destinazione: Path) -> Path | None:
    cartella = Path(settings.media_dir)
    if not cartella.is_dir() or not any(cartella.iterdir()):
        print("Nessuna foto da salvare")
        return None
    with tarfile.open(destinazione, "w:gz") as archivio:
        archivio.add(cartella, arcname="media")
    return destinazione


def ruota(cartella: Path, quante: int) -> int:
    """Tiene le ultime N copie. Senza, il disco si riempie e l'app si ferma."""
    copie = sorted(
        (p for p in cartella.iterdir() if p.is_dir() and p.name.startswith("20")),
        reverse=True,
    )
    eliminate = 0
    for vecchia in copie[quante:]:
        shutil.rmtree(vecchia)
        eliminate += 1
    return eliminate


def dimensione(percorso: Path) -> str:
    mb = percorso.stat().st_size / (1024 * 1024)
    return f"{mb:.1f} MB" if mb >= 0.1 else f"{percorso.stat().st_size / 1024:.0f} kB"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dove", default="backup", help="Cartella di destinazione")
    parser.add_argument(
        "--tieni", type=int, default=14, help="Quante copie conservare (default 14)"
    )
    args = parser.parse_args()

    momento = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    cartella = Path(args.dove) / momento
    cartella.mkdir(parents=True, exist_ok=True)

    print(f"Backup in {cartella}")

    db = salva_database(cartella / "guardlink.db")
    if db:
        print(f"  database: {dimensione(db)}")

    foto = salva_foto(cartella / "media.tar.gz")
    if foto:
        print(f"  foto:     {dimensione(foto)}")

    if not db and not foto:
        # Una cartella vuota farebbe credere che una copia esista.
        cartella.rmdir()
        print("Niente da salvare.")
        return 1

    eliminate = ruota(Path(args.dove), args.tieni)
    if eliminate:
        print(f"  copie vecchie rimosse: {eliminate}")

    print("\nFatto. Ricordati di portarne una copia FUORI da questo server:")
    print("  un backup che sta sullo stesso disco non serve a niente se il")
    print("  disco si rompe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
