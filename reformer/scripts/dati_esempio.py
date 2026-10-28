"""Riempie un database **di prova** con clienti e prenotazioni finte.

    python -m reformer.scripts.dati_esempio

Serve a provare l'app e a fare le schermate. Crea Greta ed Elisa (staff, con
password `demo1234`), una quindicina di clienti `@example.com` e le loro
prenotazioni delle prossime settimane. **Mai sul server vero**: se trova già
degli account si ferma.
"""

import random
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from reformer.core.security import hash_password
from reformer.db.init_db import init_db
from reformer.db.session import SessionLocal
from reformer.dominio import orario
from reformer.models import Avviso, Prenotazione, Ruolo, StatoPrenotazione, Utente
from reformer.servizi import regole

NOMI = [
    ("Sofia", "Marini"), ("Chiara", "Rinaldi"), ("Martina", "Ferri"), ("Laura", "De Santis"),
    ("Valentina", "Greco"), ("Francesca", "Lombardi"), ("Alessia", "Conti"), ("Giorgia", "Fabbri"),
    ("Federica", "Moretti"), ("Silvia", "Galli"), ("Paola", "Testa"), ("Roberta", "Villa"),
    ("Serena", "Bruno"), ("Elena", "Pace"), ("Marta", "Leone"),
]


def main() -> int:
    init_db()
    caso = random.Random(2026)
    with SessionLocal() as db:
        if db.scalar(select(func.count(Utente.id))):
            print("Il database ha già degli account: non aggiungo dati finti.")
            return 1
        adesso = datetime.now(timezone.utc)
        pwd = hash_password("demo1234")
        staff = []
        for nome, cognome, email in [
            ("Greta", "Lorenzetti", "greta.lorenzetti@icloud.com"),
            ("Elisa", "Bonacci", "elisabonacci@yahoo.it"),
        ]:
            u = Utente(email=email, password_hash=pwd, nome=nome, cognome=cognome, telefono="",
                       ruolo=Ruolo.STAFF, email_verificata_il=adesso, privacy_accettata_il=adesso)
            db.add(u)
            staff.append(u)
        clienti = []
        for nome, cognome in NOMI:
            u = Utente(
                email=f"{nome.lower()}.{cognome.lower().replace(' ', '')}@example.com",
                password_hash=pwd, nome=nome, cognome=cognome,
                telefono=f"3{caso.randint(10, 99)} {caso.randint(100, 999)} {caso.randint(1000, 9999)}",
                email_verificata_il=adesso, privacy_accettata_il=adesso,
                creato_il=adesso - timedelta(days=caso.randint(1, 60)),
            )
            db.add(u)
            clienti.append(u)
        db.commit()
        for c in clienti:
            regole.imposta_saldo(db, c, caso.choice(staff), lezioni=caso.choice([4, 6, 8, 10]), nota="Pacchetto pagato in studio")

        # Due settimane passate (con presenze) e tre future.
        da = orario.oggi() - timedelta(days=14)
        for lez in regole.lezioni_nel_periodo(db, da, 35):
            futura = lez.inizio > adesso
            giorni = (lez.inizio - adesso).days
            quante = min(3, caso.randint(0, 3) + (1 if giorni < 5 else 0)) if futura else caso.randint(2, 3)
            for c in caso.sample(clienti, quante):
                db.add(Prenotazione(lezione_id=lez.id, utente_id=c.id,
                                    presente=None if futura else caso.random() > 0.08))
                regole.muovi_saldo(db, c, -1, "Prenotazione", lezione=lez)
            if caso.random() < 0.3:
                lez.titolo = caso.choice(["Pilates · Principianti", "Pilates · Postura e schiena",
                                          "Pilates · Total body", "Pilates · Core e addome"])
            db.commit()

        # Qualcuna in lista d'attesa sulle lezioni piene di questa settimana.
        for lez in regole.lezioni_nel_periodo(db, orario.oggi() + timedelta(days=1), 6):
            if lez.liberi == 0 and caso.random() < 0.5:
                dentro = {p.utente_id for p in lez.attive}
                fuori = [c for c in clienti if c.id not in dentro]
                regole.entra_in_attesa(db, lez.id, caso.choice(fuori))

        # Il saldo finale come quello di uno studio vero: qualche lezione
        # rimasta a testa, e una cliente da saldare.
        for c in clienti:
            regole.imposta_saldo(db, c, caso.choice(staff), lezioni=caso.randint(1, 9), nota="Pacchetto pagato in studio")
        regole.imposta_saldo(db, clienti[10], staff[0], lezioni=-1, nota="Ha prenotato senza pacchetto")
        db.add(Avviso(autore_id=staff[0].id, testo=(
            "Benvenute nella nuova app! Da oggi le lezioni si prenotano da qui. "
            "Per qualsiasi dubbio scriveteci su WhatsApp."
        )))
        db.commit()
        attive = db.scalar(select(func.count(Prenotazione.id)).where(Prenotazione.stato == StatoPrenotazione.ATTIVA))
        print(f"Fatto: 2 staff, {len(clienti)} clienti, {attive} prenotazioni. Password di tutte: demo1234")
    return 0


if __name__ == "__main__":
    sys.exit(main())
