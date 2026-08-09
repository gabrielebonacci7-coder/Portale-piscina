"""Consenso, esportazione dei dati e cancellazione dell'account.

La parte delicata è la cancellazione: deve portare via i dati personali senza
danneggiare quelli di chi ha lavorato con la persona che se ne va.
"""

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.privacy import NOME_ANONIMO, VERSIONE_INFORMATIVA
from app.models import Recensione, Utente
from tests.conftest import auth, login, registra


def cancella(client, token, password="password123", conferma="CANCELLA"):
    return client.request(
        "DELETE",
        "/auth/me",
        json={"password": password, "conferma": conferma},
        headers=auth(token),
    )


# --- Consenso ---------------------------------------------------------------
def test_senza_consenso_non_ci_si_iscrive(client):
    r = client.post(
        "/auth/registrazione",
        json={
            "email": "nuovo@test.it",
            "password": "password123",
            "tipo": "bagnino",
            "accetta_privacy": False,
        },
    )
    assert r.status_code == 422
    assert "informativa" in r.text


def test_il_consenso_non_si_puo_omettere(client):
    """Niente valore di default: un campo assente non è un sì."""
    r = client.post(
        "/auth/registrazione",
        json={"email": "nuovo@test.it", "password": "password123", "tipo": "bagnino"},
    )
    assert r.status_code == 422


def test_si_salva_quando_e_quale_versione(client):
    dati = registra(client, "nuovo@test.it", "bagnino")
    assert dati["privacy_accettata_il"] is not None
    assert dati["privacy_versione"] == VERSIONE_INFORMATIVA


def test_la_pagina_dell_informativa_e_raggiungibile(client):
    r = client.get("/privacy.html")
    assert r.status_code == 200
    assert "Informativa privacy" in r.text


# --- Esportazione -----------------------------------------------------------
def test_esportazione_contiene_i_propri_dati(client, bagnino):
    r = client.get("/auth/esporta", headers=auth(bagnino["token"]))
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]

    dati = r.json()
    assert dati["account"]["email"] == "bagnino@test.it"
    assert dati["profilo"]["nome"] == "Marco"
    assert dati["profilo"]["zone"] == ["EUR"]
    assert [b["tipo"] for b in dati["brevetti"]] == ["MIP"]
    # Le date escono in un formato leggibile, non come oggetti Python.
    assert isinstance(dati["account"]["creato_il"], str)


def test_esportazione_senza_token(client):
    assert client.get("/auth/esporta").status_code == 401


def test_esportazione_non_regala_i_messaggi_ricevuti(client, bagnino, piscina):
    """Escono solo i propri: quelli altrui sono dati di chi li ha scritti."""
    conv = client.post(
        "/conversazioni",
        json={"destinatario_id": bagnino["utente_id"], "testo": "Ti scrivo io"},
        headers=auth(piscina["token"]),
    )
    assert conv.status_code == 201
    client.post(
        f"/conversazioni/{conv.json()['id']}/messaggi",
        json={"testo": "Rispondo io"},
        headers=auth(bagnino["token"]),
    )

    dati = client.get("/auth/esporta", headers=auth(bagnino["token"])).json()
    testi = [m["testo"] for m in dati["messaggi_inviati"]]
    assert testi == ["Rispondo io"]


# --- Cancellazione ----------------------------------------------------------
def test_il_riepilogo_dice_cosa_succede(client, bagnino):
    r = client.get("/auth/cancellazione/riepilogo", headers=auth(bagnino["token"]))
    assert r.status_code == 200
    assert r.json()["profilo"] is True


def test_serve_la_password(client, bagnino):
    r = cancella(client, bagnino["token"], password="sbagliata")
    assert r.status_code == 400
    assert client.get("/auth/me", headers=auth(bagnino["token"])).status_code == 200


def test_serve_scrivere_cancella(client, bagnino):
    r = cancella(client, bagnino["token"], conferma="ok")
    assert r.status_code == 422


def test_cancellazione_toglie_i_dati_personali(client, db_engine, bagnino):
    assert cancella(client, bagnino["token"]).status_code == 204

    # Il token non vale più, e nemmeno la vecchia password.
    assert client.get("/auth/me", headers=auth(bagnino["token"])).status_code == 403
    r = client.post(
        "/auth/login", json={"email": "bagnino@test.it", "password": "password123"}
    )
    assert r.status_code == 401

    Sessione = sessionmaker(bind=db_engine)
    with Sessione() as db:
        utente = db.get(Utente, bagnino["utente_id"])
        assert utente.cancellato_il is not None
        assert utente.email == f"cancellato-{utente.id}@guardlink.invalid"
        assert utente.telefono is None
        assert utente.password_hash is None
        assert utente.attivo is False
        # Il profilo, e con lui brevetti ed esperienze, non c'è più.
        assert utente.profilo_bagnino is None
        assert utente.nome_visualizzato == NOME_ANONIMO


def test_il_profilo_pubblico_sparisce(client, bagnino, piscina):
    profilo_id = bagnino["profilo_id"]
    assert client.get(f"/bagnini/{profilo_id}", headers=auth(piscina["token"])).status_code == 200

    cancella(client, bagnino["token"])

    r = client.get(f"/bagnini/{profilo_id}", headers=auth(piscina["token"]))
    assert r.status_code == 404
    # E non compare più nemmeno nell'elenco.
    elenco = client.get("/bagnini", headers=auth(piscina["token"])).json()
    assert elenco["totale"] == 0


def test_le_recensioni_scritte_restano_ma_senza_nome(client, db_engine, bagnino, piscina):
    """Il punto più delicato: la reputazione della struttura non è del bagnino.

    Se cancellare l'account azzerasse le recensioni date, chiunque potrebbe
    togliere un giudizio scomodo iscrivendosi di nuovo il giorno dopo.
    """
    annuncio = client.post(
        "/annunci",
        json={
            "titolo": "Turno di prova",
            "tipo": "piscina_cerca_bagnino",
            "data_inizio": "2030-07-01T09:00:00Z",
            "zona_id": 1,
            "compenso": 12.5,
            "compenso_tipo": "orario",
        },
        headers=auth(piscina["token"]),
    ).json()
    assegna = client.post(
        f"/annunci/{annuncio['id']}/assegna",
        params={"assegnatario_id": bagnino["utente_id"]},
        headers=auth(piscina["token"]),
    )
    assert assegna.status_code == 200, assegna.text
    recensione = client.post(
        "/recensioni",
        json={
            "destinatario_id": piscina["utente_id"],
            "annuncio_id": annuncio["id"],
            "stelle": 2,
            "commento": "Pagamento in ritardo",
        },
        headers=auth(bagnino["token"]),
    )
    assert recensione.status_code == 201

    cancella(client, bagnino["token"])

    Sessione = sessionmaker(bind=db_engine)
    with Sessione() as db:
        resta = db.scalar(select(Recensione).where(Recensione.id == recensione.json()["id"]))
        assert resta is not None
        assert resta.commento == "Pagamento in ritardo"

    # E la struttura la vede ancora, firmata "Utente cancellato".
    ricevute = client.get(
        f"/utenti/{piscina['utente_id']}/recensioni", headers=auth(piscina["token"])
    ).json()
    assert ricevute["totale"] == 1
    assert ricevute["recensioni"][0]["autore_nome"] == NOME_ANONIMO


def test_gli_annunci_aperti_spariscono(client, bagnino, piscina):
    client.post(
        "/annunci",
        json={
            "titolo": "Cerco sostituzione",
            "tipo": "bagnino_cerca_sostituzione",
            "data_inizio": "2030-07-01T09:00:00Z",
            "zona_id": 1,
        },
        headers=auth(bagnino["token"]),
    )
    prima = client.get("/annunci", headers=auth(piscina["token"])).json()["totale"]
    assert prima == 1

    cancella(client, bagnino["token"])

    dopo = client.get("/annunci", headers=auth(piscina["token"])).json()["totale"]
    assert dopo == 0


def test_lo_staff_non_puo_cancellarsi_da_solo(client, db_engine):
    """Prima si toglie il ruolo, altrimenti il pannello resta senza nessuno."""
    registra(client, "gestione@test.it", "piscina")
    Sessione = sessionmaker(bind=db_engine)
    with Sessione() as db:
        from app.models import Ruolo

        utente = db.scalar(select(Utente).where(Utente.email == "gestione@test.it"))
        utente.ruolo = Ruolo.STAFF
        db.commit()

    r = cancella(client, login(client, "gestione@test.it"))
    assert r.status_code == 409
