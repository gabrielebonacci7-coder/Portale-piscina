"""Dare o togliere il ruolo staff a mano.

    python -m reformer.scripts.crea_staff --elenco
    python -m reformer.scripts.crea_staff email@esempio.it          # dà il ruolo
    python -m reformer.scripts.crea_staff email@esempio.it --togli

Di solito non serve: Greta ed Elisa diventano staff da sole quando
confermano l'email (REFORMER_EMAIL_STAFF). Questo comando è la riserva, per
esempio se le email non partono ancora. La persona deve essersi già
registrata dall'app.

Non esiste una pagina che faccia la stessa cosa, apposta: se ci fosse,
basterebbe un account rubato per prendersi il gestionale.
"""

import argparse
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from reformer.db.init_db import init_db
from reformer.db.session import SessionLocal
from reformer.models import Ruolo, Utente


def main() -> int:
    p = argparse.ArgumentParser(description="Ruolo staff")
    p.add_argument("email", nargs="?")
    p.add_argument("--togli", action="store_true")
    p.add_argument("--elenco", action="store_true")
    a = p.parse_args()
    init_db()
    with SessionLocal() as db:
        if a.elenco or not a.email:
            for u in db.scalars(select(Utente).where(Utente.ruolo == Ruolo.STAFF)):
                print(f"{u.email}  ({u.nome_completo})")
            return 0
        u = db.scalar(select(Utente).where(Utente.email == a.email.strip().lower()))
        if u is None:
            print(f"Nessun account con {a.email}: deve prima registrarsi dall'app.")
            return 1
        if a.togli:
            u.ruolo = Ruolo.CLIENTE
        else:
            u.ruolo = Ruolo.STAFF
            # Il comando lo lancia chi ha accesso al server: vale come conferma.
            u.email_verificata_il = u.email_verificata_il or datetime.now(timezone.utc)
        db.commit()
        print(f"{u.email}: ora è {u.ruolo.value}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
