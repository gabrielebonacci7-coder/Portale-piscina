"""Popola il database con dati di esempio, per provare lo schema.

    python -m scripts.seed_demo
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import (
    Annuncio,
    Brevetto,
    Disponibilita,
    Esperienza,
    ProfiloBagnino,
    ProfiloPiscina,
    Recensione,
    StatoAnnuncio,
    TipoAnnuncio,
    TipoBrevetto,
    TipoCompenso,
    TipoStruttura,
    TipoTurno,
    TipoUtente,
    Utente,
    Zona,
)


# Password condivisa dagli account di esempio, per provare il login.
PASSWORD_DEMO = "demo1234"


def main() -> None:
    init_db()

    with SessionLocal() as db:
        if db.scalar(select(Utente).limit(1)):
            print("Dati già presenti, nessun inserimento.")
            return

        eur = db.scalar(select(Zona).where(Zona.nome == "EUR"))
        ostia = db.scalar(select(Zona).where(Zona.nome == "Ostia / Acilia"))

        # --- Bagnino ------------------------------------------------------
        u_bagnino = Utente(
            email="marco.rossi@example.com",
            telefono="+39 333 1112223",
            password_hash=hash_password(PASSWORD_DEMO),
            tipo=TipoUtente.BAGNINO,
        )
        bagnino = ProfiloBagnino(
            utente=u_bagnino,
            nome="Marco",
            cognome="Rossi",
            data_nascita=date(1996, 4, 18),
            anni_esperienza=6,
            bio="Bagnino con esperienza in piscine comunali e hotel.",
            disponibile_chiamata_singola=True,
            zone=[z for z in (eur, ostia) if z is not None],
        )
        bagnino.brevetti.append(
            Brevetto(
                tipo=TipoBrevetto.MIP,
                ente="FIN",
                numero="RM-123456",
                data_rilascio=date.today() - timedelta(days=200),
                data_scadenza=date.today() + timedelta(days=530),
                verificato=True,
            )
        )
        bagnino.esperienze.append(
            Esperienza(
                struttura="Piscina Comunale EUR",
                zona="EUR",
                mansione="Assistente bagnanti",
                data_inizio=date(2021, 6, 1),
                data_fine=date(2023, 9, 15),
                stagioni=3,
            )
        )
        bagnino.disponibilita.extend(
            [
                Disponibilita(giorno_settimana=g, ora_inizio=time(14, 0), ora_fine=time(20, 0))
                for g in (0, 2, 4)
            ]
        )

        # --- Piscina ------------------------------------------------------
        u_piscina = Utente(
            email="info@aquacenter.example",
            telefono="+39 06 5551234",
            password_hash=hash_password(PASSWORD_DEMO),
            tipo=TipoUtente.PISCINA,
            telefono_pubblico=True,
        )
        piscina = ProfiloPiscina(
            utente=u_piscina,
            nome_struttura="Aqua Center EUR",
            tipo_struttura=TipoStruttura.CENTRO_SPORTIVO,
            zona=eur,
            indirizzo="Viale America 50",
            numero_vasche=2,
            referente_nome="Laura Bianchi",
            referente_ruolo="Gestore",
            referente_telefono="+39 06 5551234",
        )

        # --- Annuncio -----------------------------------------------------
        inizio = datetime.now(timezone.utc) + timedelta(days=2, hours=8)
        annuncio = Annuncio(
            autore=u_piscina,
            piscina=piscina,
            tipo=TipoAnnuncio.PISCINA_CERCA_BAGNINO,
            titolo="Sostituzione urgente turno pomeridiano",
            data_inizio=inizio,
            data_fine=inizio + timedelta(hours=5),
            zona=eur,
            indirizzo="Viale America 50",
            compenso=Decimal("12.50"),
            compenso_tipo=TipoCompenso.ORARIO,
            tipo_turno=TipoTurno.SOSTITUZIONE_URGENTE,
            brevetto_richiesto=TipoBrevetto.P,
            urgente=True,
            note="Vasca da 25m, necessaria esperienza con corsi bambini.",
            stato=StatoAnnuncio.APERTO,
        )

        # Un secondo turno, già svolto e chiuso: è quello a cui si aggancia
        # la recensione, dato che si recensisce solo dopo un turno concluso.
        passato = datetime.now(timezone.utc) - timedelta(days=20)
        concluso = Annuncio(
            autore=u_piscina,
            piscina=piscina,
            tipo=TipoAnnuncio.PISCINA_CERCA_BAGNINO,
            titolo="Turno serale evento estivo",
            data_inizio=passato,
            data_fine=passato + timedelta(hours=4),
            zona=eur,
            compenso=Decimal("14.00"),
            compenso_tipo=TipoCompenso.ORARIO,
            tipo_turno=TipoTurno.EVENTO_SERALE,
            stato=StatoAnnuncio.CHIUSO,
            assegnato_a=u_bagnino,
        )

        db.add_all([u_bagnino, bagnino, u_piscina, piscina, annuncio, concluso])
        db.flush()

        # --- Recensione incrociata ----------------------------------------
        db.add(
            Recensione(
                autore_id=u_piscina.id,
                destinatario_id=u_bagnino.id,
                annuncio_id=concluso.id,
                stelle=5,
                commento="Puntuale e attento, lo richiameremo.",
                voto_puntualita=5,
                voto_professionalita=5,
            )
        )
        db.commit()

        print(f"Bagnino: {bagnino.nome_completo}, {bagnino.eta} anni, abilitato={bagnino.abilitato}")
        print(f"Struttura: {piscina.nome_struttura} ({piscina.tipo_struttura.value})")
        print(f"Annuncio: {annuncio.titolo} — {annuncio.compenso} €/h, aperto={annuncio.aperto}")
        print(f"\nAccessi di prova (password: {PASSWORD_DEMO}):")
        print(f"  bagnino  -> {u_bagnino.email}")
        print(f"  piscina  -> {u_piscina.email}")


if __name__ == "__main__":
    main()
