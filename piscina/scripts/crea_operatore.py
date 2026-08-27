"""Crea (o aggiorna) un account dello staff.

    python -m piscina.scripts.crea_operatore "Gabriele" gabriele@example.com

La password si digita al momento e non compare né nella riga di comando né
nella cronologia della shell.
"""

import getpass
import sys

from sqlalchemy import select

from piscina.core.security import hash_password
from piscina.db.init_db import init_db
from piscina.db.session import SessionLocal
from piscina.models import Operatore


def main(argomenti: list[str]) -> int:
    if len(argomenti) != 2:
        print(__doc__)
        return 2
    nome, email = argomenti[0].strip(), argomenti[1].strip().lower()

    password = getpass.getpass("Password: ")
    if len(password) < 8:
        print("La password deve avere almeno 8 caratteri.")
        return 1
    if password != getpass.getpass("Ripeti la password: "):
        print("Le due password non coincidono.")
        return 1

    init_db()
    with SessionLocal() as db:
        operatore = db.scalar(select(Operatore).where(Operatore.email == email))
        if operatore is None:
            operatore = Operatore(email=email, nome=nome)
            db.add(operatore)
            azione = "creato"
        else:
            operatore.nome = nome
            azione = "aggiornato"
        operatore.password_hash = hash_password(password)
        operatore.attivo = True
        db.commit()

    print(f"Operatore {azione}: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
