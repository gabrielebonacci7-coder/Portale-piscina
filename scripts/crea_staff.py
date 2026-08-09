"""Assegna o toglie il permesso di staff a un account.

    python -m scripts.crea_staff gestione@guardlink.it
    python -m scripts.crea_staff gestione@guardlink.it --togli
    python -m scripts.crea_staff --elenco

Il ruolo si dà **solo** da qui, cioè solo da chi ha accesso al server: non
esiste nessuna rotta HTTP che promuova qualcuno a staff. Se ci fosse, basterebbe
un account compromesso per prendersi il pannello di gestione.

L'account deve esistere già: ci si registra normalmente dall'app e poi si esegue
questo comando. Così la password la sceglie la persona, e qui dentro non ci
passa mai.
"""

import argparse
import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Ruolo, Utente


def elenca() -> None:
    with SessionLocal() as db:
        membri = db.scalars(
            select(Utente).where(Utente.ruolo == Ruolo.STAFF).order_by(Utente.id)
        ).all()
    if not membri:
        print("Nessun account staff. Assegnalo con: python -m scripts.crea_staff EMAIL")
        return
    print(f"Staff ({len(membri)}):")
    for utente in membri:
        stato = "attivo" if utente.attivo else "SOSPESO"
        print(f"  #{utente.id}  {utente.email}  ({utente.tipo.value}, {stato})")


def imposta(email: str, staff: bool) -> int:
    email = email.lower().strip()
    with SessionLocal() as db:
        utente = db.scalar(select(Utente).where(Utente.email == email))
        if utente is None:
            print(f"Nessun account con l'email {email}.", file=sys.stderr)
            print(
                "Registrati prima dall'app, poi rilancia questo comando.", file=sys.stderr
            )
            return 1

        ruolo = Ruolo.STAFF if staff else Ruolo.UTENTE
        if utente.ruolo == ruolo:
            print(f"{email} è già '{ruolo.value}': niente da fare.")
            return 0

        # Togliere il ruolo all'ultimo membro rimasto chiuderebbe il pannello a
        # tutti, e per riaprirlo servirebbe di nuovo accesso al server.
        if not staff:
            rimasti = db.scalar(
                select(Utente.id).where(Utente.ruolo == Ruolo.STAFF, Utente.id != utente.id)
            )
            if rimasti is None:
                print(
                    "È l'unico account staff rimasto: assegna prima il ruolo a "
                    "qualcun altro.",
                    file=sys.stderr,
                )
                return 1

        utente.ruolo = ruolo
        db.commit()

    verbo = "assegnato a" if staff else "tolto a"
    print(f"Ruolo staff {verbo} {email}.")
    if staff:
        print("Rientra nell'app: nel menù comparirà la scheda 'Gestione'.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("email", nargs="?", help="Email di un account già registrato")
    parser.add_argument(
        "--togli", action="store_true", help="Riporta l'account a utente normale"
    )
    parser.add_argument("--elenco", action="store_true", help="Mostra chi è staff")
    args = parser.parse_args()

    if args.elenco:
        elenca()
        return 0
    if not args.email:
        parser.error("indica un'email, oppure usa --elenco")
    return imposta(args.email, staff=not args.togli)


if __name__ == "__main__":
    raise SystemExit(main())
