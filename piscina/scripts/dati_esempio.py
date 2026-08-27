"""Riempie qualche postazione, per vedere la mappa con i colori accesi.

    python -m piscina.scripts.dati_esempio

Non serve in esercizio: serve a provare l'app e a fare le schermate.
"""

from datetime import timedelta

from piscina.crud import prenotazioni as crud
from piscina.db.init_db import init_db
from piscina.db.session import SessionLocal
from piscina.dominio.disponibilita import GIORNATA, MATTINA, POMERIGGIO
from piscina.dominio.orologio import oggi

ESEMPI = [
    # (postazioni, lettini, fascia, nome, telefono, email, persone)
    (["A1", "A2"], 2, GIORNATA, "Marco Rossi", "333 1234567", "marco.rossi@example.com", 4),
    (["A5"], 3, GIORNATA, "Giulia Conti", "347 7654321", "giulia.conti@example.com", 3),
    (["B3"], 1, MATTINA, "Anna Ferri", "349 1112233", "anna.ferri@example.com", 2),
    (["B4"], 2, POMERIGGIO, "Luca Neri", "340 9988776", "luca.neri@example.com", 2),
    (["C2", "C3"], 2, GIORNATA, "Famiglia Esposito", "331 4455667", "esposito@example.com", 6),
    (["E1"], 0, MATTINA, "Sara Bianchi", "338 5566778", "sara.bianchi@example.com", 1),
    (["S1", "S2"], 0, GIORNATA, "Paolo Greco", "335 2233445", "paolo.greco@example.com", 2),
]


def main() -> None:
    init_db()
    domani = oggi() + timedelta(days=1)
    creati = 0
    with SessionLocal() as db:
        for codici, lettini, fascia, nome, telefono, email, persone in ESEMPI:
            for giorno in (oggi(), domani):
                try:
                    crud.crea(
                        db,
                        giorno=giorno,
                        fascia=fascia,
                        scelte=[crud.Scelta(codice=c, lettini=lettini) for c in codici],
                        nome=nome,
                        telefono=telefono,
                        email=email,
                        persone=persone,
                    )
                    creati += 1
                except (crud.RichiestaNonValida, crud.PostoOccupato) as e:
                    print(f"  salto {codici} del {giorno}: {e}")
    print(f"{creati} prenotazioni di esempio create.")


if __name__ == "__main__":
    main()
