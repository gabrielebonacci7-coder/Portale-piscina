"""Pannello di gestione: chi ci entra, cosa può fare, cosa resta scritto."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.models import Ruolo, Utente
from tests.conftest import auth, login, registra


def promuovi(db_engine, email: str) -> None:
    """Assegna il ruolo staff come fa `scripts.crea_staff`: direttamente sul db."""
    Sessione = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    with Sessione() as db:
        utente = db.scalar(select(Utente).where(Utente.email == email))
        utente.ruolo = Ruolo.STAFF
        db.commit()


@pytest.fixture
def staff(client, db_engine):
    """Un account normale a cui è stato dato il permesso di staff."""
    utente = registra(client, "gestione@test.it", "piscina")
    promuovi(db_engine, "gestione@test.it")
    return {"token": login(client, "gestione@test.it"), "utente_id": utente["id"]}


def test_senza_ruolo_il_pannello_non_esiste(client, bagnino):
    """A un utente normale il pannello risponde 404, non 403.

    Un 403 confermerebbe che l'indirizzo esiste; 404 non dice nulla.
    """
    r = client.get("/staff/riepilogo", headers=auth(bagnino["token"]))
    assert r.status_code == 404


def test_senza_token_serve_il_login(client):
    assert client.get("/staff/riepilogo").status_code == 401


def test_la_registrazione_non_permette_di_farsi_staff(client):
    """Il campo `ruolo` mandato in registrazione viene ignorato."""
    r = client.post(
        "/auth/registrazione",
        json={
            "email": "furbo@test.it",
            "password": "password123",
            "tipo": "bagnino",
            "ruolo": "staff",
        },
    )
    assert r.status_code == 201
    assert r.json()["ruolo"] == "utente"


def test_riepilogo(client, staff, bagnino, piscina):
    r = client.get("/staff/riepilogo", headers=auth(staff["token"]))
    assert r.status_code == 200
    dati = r.json()
    # bagnino + piscina + lo staff stesso
    assert dati["utenti"] == 3
    assert dati["bagnini"] == 1
    assert dati["brevetti_da_verificare"] == 1
    assert dati["sospesi"] == 0


def test_cerca_utenti_per_nome_e_filtra_per_tipo(client, staff, bagnino, piscina):
    r = client.get("/staff/utenti", params={"q": "rossi"}, headers=auth(staff["token"]))
    assert r.status_code == 200
    assert [u["nome"] for u in r.json()["elementi"]] == ["Marco Rossi"]

    r = client.get("/staff/utenti", params={"tipo": "piscina"}, headers=auth(staff["token"]))
    # la struttura di prova e l'account dello staff, che è di tipo piscina
    assert r.json()["totale"] == 2

    r = client.get("/staff/utenti", params={"q": "aqua"}, headers=auth(staff["token"]))
    elenco = r.json()["elementi"]
    assert len(elenco) == 1
    assert elenco[0]["nome"] == "Aqua Test"


def test_coda_brevetti_e_verifica(client, staff, bagnino):
    r = client.get("/staff/brevetti", headers=auth(staff["token"]))
    assert r.status_code == 200
    coda = r.json()["elementi"]
    assert len(coda) == 1
    assert coda[0]["nome"] == "Marco Rossi"
    assert coda[0]["email"] == "bagnino@test.it"
    assert coda[0]["verificato"] is False

    brevetto_id = coda[0]["id"]
    r = client.post(
        f"/staff/brevetti/{brevetto_id}/verifica",
        json={"valore": True, "motivo": "Visto originale FIN"},
        headers=auth(staff["token"]),
    )
    assert r.status_code == 200
    assert r.json()["verificato"] is True

    # Verificato: esce dalla coda.
    r = client.get("/staff/brevetti", headers=auth(staff["token"]))
    assert r.json()["totale"] == 0
    # Ma si ritrova chiedendo tutti.
    r = client.get(
        "/staff/brevetti", params={"solo_da_verificare": False}, headers=auth(staff["token"])
    )
    assert r.json()["totale"] == 1


def test_verifica_brevetto_inesistente(client, staff):
    r = client.post(
        "/staff/brevetti/999/verifica", json={"valore": True}, headers=auth(staff["token"])
    )
    assert r.status_code == 404


def test_sospensione_blocca_l_accesso_e_la_riattivazione_lo_ridà(client, staff, bagnino):
    r = client.post(
        f"/staff/utenti/{bagnino['utente_id']}/stato",
        json={"attivo": False, "motivo": "Brevetto falso"},
        headers=auth(staff["token"]),
    )
    assert r.status_code == 200
    assert r.json()["attivo"] is False

    # Il token che aveva in mano smette di funzionare.
    assert client.get("/auth/me", headers=auth(bagnino["token"])).status_code == 403

    r = client.post(
        f"/staff/utenti/{bagnino['utente_id']}/stato",
        json={"attivo": True, "motivo": "Chiarito"},
        headers=auth(staff["token"]),
    )
    assert r.json()["attivo"] is True
    assert client.get("/auth/me", headers=auth(bagnino["token"])).status_code == 200


def test_sospendere_richiede_un_motivo(client, staff, bagnino):
    r = client.post(
        f"/staff/utenti/{bagnino['utente_id']}/stato",
        json={"attivo": False},
        headers=auth(staff["token"]),
    )
    assert r.status_code == 422


def test_non_si_agisce_su_se_stessi_ne_sugli_altri_staff(client, staff, db_engine):
    r = client.post(
        f"/staff/utenti/{staff['utente_id']}/stato",
        json={"attivo": False, "motivo": "test"},
        headers=auth(staff["token"]),
    )
    assert r.status_code == 422

    registra(client, "collega@test.it", "bagnino")
    promuovi(db_engine, "collega@test.it")
    collega_id = client.post(
        "/auth/login", json={"email": "collega@test.it", "password": "password123"}
    ).json()["utente"]["id"]

    r = client.post(
        f"/staff/utenti/{collega_id}/stato",
        json={"attivo": False, "motivo": "test"},
        headers=auth(staff["token"]),
    )
    assert r.status_code == 403


def test_verifica_utente(client, staff, piscina):
    r = client.post(
        f"/staff/utenti/{piscina['utente_id']}/verifica",
        json={"valore": True, "motivo": "Vista partita IVA"},
        headers=auth(staff["token"]),
    )
    assert r.status_code == 200
    assert r.json()["verificato"] is True


def test_ogni_azione_finisce_nel_registro(client, staff, bagnino):
    client.post(
        f"/staff/utenti/{bagnino['utente_id']}/verifica",
        json={"valore": True},
        headers=auth(staff["token"]),
    )
    client.post(
        f"/staff/utenti/{bagnino['utente_id']}/stato",
        json={"attivo": False, "motivo": "Segnalazioni ripetute"},
        headers=auth(staff["token"]),
    )

    r = client.get("/staff/registro", headers=auth(staff["token"]))
    assert r.status_code == 200
    righe = r.json()["elementi"]
    assert r.json()["totale"] == 2
    # La più recente in cima.
    assert righe[0]["azione"] == "utente_sospeso"
    assert righe[0]["motivo"] == "Segnalazioni ripetute"
    assert righe[0]["oggetto_etichetta"] == "Marco Rossi"
    assert righe[0]["staff_email"] == "gestione@test.it"
    assert righe[1]["azione"] == "utente_verificato"


def test_lo_staff_resta_un_utente_normale(client, staff):
    """Il permesso non cambia il tipo di account: la piscina resta una piscina."""
    r = client.get("/auth/me", headers=auth(staff["token"]))
    assert r.json()["tipo"] == "piscina"
    assert r.json()["ruolo"] == "staff"
