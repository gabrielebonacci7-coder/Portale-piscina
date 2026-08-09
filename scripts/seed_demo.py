"""Popola il database con dati di esempio, per provare lo schema.

    python -m scripts.seed_demo
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from scripts import foto_demo

from app.core.immagini import salva_immagine
from app.core.privacy import VERSIONE_INFORMATIVA
from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import (
    Annuncio,
    Brevetto,
    Candidatura,
    Conversazione,
    Disponibilita,
    Esperienza,
    FotoPiscina,
    Messaggio,
    Partecipante,
    ProfiloBagnino,
    ProfiloPiscina,
    Recensione,
    StatoAnnuncio,
    TipoAnnuncio,
    TipoBrevetto,
    TipoCompenso,
    TipoFoto,
    TipoStruttura,
    TipoTurno,
    TipoUtente,
    Utente,
    Zona,
)


# Password condivisa dagli account di esempio, per provare il login.
PASSWORD_DEMO = "demo1234"


def fra_giorni(giorni: int, ora_utc: int) -> datetime:
    """Una data futura a un'ora sensata invece che "adesso più N ore".

    L'ora è in UTC: 7 e 12 diventano le 9 e le 14 in Italia d'estate, orari
    plausibili per un turno in piscina in entrambi i fusi.
    """
    d = datetime.now(timezone.utc) + timedelta(days=giorni)
    return d.replace(hour=ora_utc, minute=0, second=0, microsecond=0)


def main() -> None:
    init_db()

    with SessionLocal() as db:
        if db.scalar(select(Utente).limit(1)):
            print("Dati già presenti, nessun inserimento.")
            return

        eur = db.scalar(select(Zona).where(Zona.nome == "EUR"))
        ostia = db.scalar(select(Zona).where(Zona.nome == "Ostia / Acilia"))
        frascati = db.scalar(select(Zona).where(Zona.nome == "Frascati"))

        # --- Bagnino ------------------------------------------------------
        u_bagnino = Utente(
            email="marco.rossi@example.com",
            telefono="+39 333 1112223",
            password_hash=hash_password(PASSWORD_DEMO),
            privacy_accettata_il=datetime.now(timezone.utc),
            privacy_versione=VERSIONE_INFORMATIVA,
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
            foto=salva_immagine(foto_demo.ritratto("M"), "bagnini"),
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
            privacy_accettata_il=datetime.now(timezone.utc),
            privacy_versione=VERSIONE_INFORMATIVA,
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
        # L'ingresso per primo: senza, la struttura non potrebbe pubblicare.
        piscina.foto = [
            FotoPiscina(
                percorso=salva_immagine(foto_demo.ingresso("AQUA CENTER"), "piscine"),
                tipo=TipoFoto.INGRESSO,
                didascalia="Ingresso su Viale America 50, cancello verde",
                ordine=0,
            ),
            FotoPiscina(
                percorso=salva_immagine(foto_demo.vasca(), "piscine"),
                tipo=TipoFoto.VASCA,
                didascalia="Vasca da 25m, sei corsie",
                ordine=1,
            ),
            FotoPiscina(
                percorso=salva_immagine(foto_demo.spogliatoi(), "piscine"),
                tipo=TipoFoto.SPOGLIATOI,
                ordine=2,
            ),
        ]

        # --- Annunci -------------------------------------------------------
        annuncio = Annuncio(
            autore=u_piscina,
            piscina=piscina,
            tipo=TipoAnnuncio.PISCINA_CERCA_BAGNINO,
            titolo="Sostituzione urgente turno pomeridiano",
            data_inizio=fra_giorni(2, 12),
            data_fine=fra_giorni(2, 17),
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

        # Qualche altro turno, così i filtri della bacheca hanno su cosa lavorare.
        altri = [
            Annuncio(
                autore=u_piscina,
                piscina=piscina,
                tipo=TipoAnnuncio.PISCINA_CERCA_BAGNINO,
                titolo="Turno mattutino corsie libere",
                data_inizio=fra_giorni(4, 7),
                data_fine=fra_giorni(4, 12),
                zona=eur,
                compenso=Decimal("13.00"),
                tipo_turno=TipoTurno.TURNO_FISSO,
                brevetto_richiesto=TipoBrevetto.P,
                note="Turno fisso, si valuta anche continuativo per la stagione.",
            ),
            Annuncio(
                autore=u_piscina,
                piscina=piscina,
                tipo=TipoAnnuncio.PISCINA_CERCA_BAGNINO,
                titolo="Festa privata a bordo vasca",
                data_inizio=fra_giorni(6, 17),
                data_fine=fra_giorni(6, 22),
                zona=ostia,
                compenso=Decimal("90.00"),
                compenso_tipo=TipoCompenso.A_TURNO,
                tipo_turno=TipoTurno.EVENTO_SERALE,
                brevetto_richiesto=TipoBrevetto.MIP,
                note="Evento con circa 60 invitati, richiesto brevetto MIP.",
            ),
            # Il verso opposto: è un bagnino a cercare chi lo copre.
            Annuncio(
                autore=u_bagnino,
                tipo=TipoAnnuncio.BAGNINO_CERCA_SOSTITUZIONE,
                titolo="Cerco sostituto per sabato mattina",
                data_inizio=fra_giorni(5, 7),
                data_fine=fra_giorni(5, 13),
                zona=ostia,
                compenso=Decimal("12.00"),
                tipo_turno=TipoTurno.WEEKEND,
                note="Turno che copro di solito io, cerco un collega per un sabato.",
            ),
        ]

        # Un secondo turno, già svolto e chiuso: è quello a cui si aggancia
        # la recensione, dato che si recensisce solo dopo un turno concluso.
        passato = fra_giorni(-20, 17)
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

        # --- Una struttura fuori Roma, ai Castelli --------------------------
        u_castelli = Utente(
            email="direzione@villaverde.example",
            telefono="+39 06 9412345",
            password_hash=hash_password(PASSWORD_DEMO),
            privacy_accettata_il=datetime.now(timezone.utc),
            privacy_versione=VERSIONE_INFORMATIVA,
            tipo=TipoUtente.PISCINA,
        )
        villa = ProfiloPiscina(
            utente=u_castelli,
            nome_struttura="Piscina Villa Verde",
            tipo_struttura=TipoStruttura.PRIVATA,
            citta="Frascati",
            zona=frascati,
            indirizzo="Via Tuscolana 12",
            numero_vasche=1,
            referente_nome="Paolo Rinaldi",
            referente_ruolo="Direttore",
        )
        villa.foto = [
            FotoPiscina(
                percorso=salva_immagine(foto_demo.ingresso("VILLA VERDE"), "piscine"),
                tipo=TipoFoto.INGRESSO,
                didascalia="Cancello su Via Tuscolana, subito dopo il bivio",
                ordine=0,
            ),
            FotoPiscina(
                percorso=salva_immagine(foto_demo.salvagente(), "piscine"),
                tipo=TipoFoto.ALTRO,
                ordine=1,
            ),
        ]
        turno_castelli = Annuncio(
            autore=u_castelli,
            piscina=villa,
            tipo=TipoAnnuncio.PISCINA_CERCA_BAGNINO,
            titolo="Stagione estiva, weekend a Frascati",
            data_inizio=fra_giorni(7, 8),
            data_fine=fra_giorni(7, 18),
            citta="Frascati",
            zona=frascati,
            indirizzo="Via Tuscolana 12",
            compenso=Decimal("110.00"),
            compenso_tipo=TipoCompenso.GIORNALIERO,
            tipo_turno=TipoTurno.STAGIONALE,
            brevetto_richiesto=TipoBrevetto.P,
            note="Vasca scoperta, servizio da giugno a settembre nei fine settimana.",
        )

        # --- Un secondo bagnino, che si candida al turno aperto -------------
        u_giulia = Utente(
            email="giulia.conti@example.com",
            telefono="+39 347 9998887",
            password_hash=hash_password(PASSWORD_DEMO),
            privacy_accettata_il=datetime.now(timezone.utc),
            privacy_versione=VERSIONE_INFORMATIVA,
            tipo=TipoUtente.BAGNINO,
        )
        giulia = ProfiloBagnino(
            utente=u_giulia,
            nome="Giulia",
            cognome="Conti",
            data_nascita=date(2001, 11, 3),
            anni_esperienza=2,
            bio="Due stagioni in piscina scoperta, disponibile nei weekend.",
            zone=[z for z in (eur,) if z is not None],
            foto=salva_immagine(foto_demo.ritratto("G", tinta=(138, 91, 18)), "bagnini"),
        )
        giulia.brevetti.append(
            Brevetto(
                tipo=TipoBrevetto.P,
                ente="FIN",
                data_rilascio=date.today() - timedelta(days=400),
                data_scadenza=date.today() + timedelta(days=330),
            )
        )

        db.add_all(
            [u_bagnino, bagnino, u_piscina, piscina, u_giulia, giulia, annuncio, concluso, *altri,
             u_castelli, villa, turno_castelli]
        )
        db.flush()

        # Il turno aperto chiede un brevetto P: Giulia ce l'ha, Marco ha il MIP
        # che lo contiene. Entrambi possono candidarsi.
        db.add_all(
            [
                Candidatura(
                    annuncio_id=annuncio.id,
                    candidato_id=u_giulia.id,
                    messaggio="Sono libera quel pomeriggio, abito all'EUR.",
                ),
                Candidatura(
                    annuncio_id=annuncio.id,
                    candidato_id=u_bagnino.id,
                    messaggio="Disponibile, ho già lavorato da voi.",
                ),
            ]
        )

        # --- Una conversazione già avviata ---------------------------------
        scambio = [
            (u_piscina.id, "Ciao Giulia, ho visto la tua candidatura. Sei libera giovedì?"),
            (u_giulia.id, "Sì, dalle 14 in poi sono disponibile."),
        ]
        conversazione = Conversazione(
            annuncio_id=annuncio.id,
            ultimo_messaggio_il=datetime.now(timezone.utc),
        )
        conversazione.partecipanti = [
            Partecipante(utente_id=u_piscina.id),
            Partecipante(utente_id=u_giulia.id),
        ]
        conversazione.messaggi = [
            Messaggio(
                mittente_id=mittente,
                testo=testo,
                creato_il=datetime.now(timezone.utc) - timedelta(minutes=30 - i * 10),
            )
            for i, (mittente, testo) in enumerate(scambio)
        ]
        db.add(conversazione)

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
        print(f"  bagnino2 -> {u_giulia.email}")
        print(f"  piscina2 -> {u_castelli.email} (Castelli Romani)")


if __name__ == "__main__":
    main()
