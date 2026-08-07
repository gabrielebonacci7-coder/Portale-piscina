"""Profili bagnino e piscina: creazione, ruoli, modifica, ricerca."""

from tests.conftest import auth, login, registra


def test_bagnino_crea_e_legge_profilo(client, bagnino):
    r = client.get("/bagnini/me", headers=auth(bagnino["token"]))
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["nome"] == "Marco"
    assert corpo["abilitato"] is True  # ha un brevetto valido fino al 2030
    assert [z["nome"] for z in corpo["zone"]] == ["EUR"]


def test_piscina_non_puo_creare_profilo_bagnino(client, piscina):
    r = client.post(
        "/bagnini",
        json={"nome": "Tizio", "cognome": "Caio"},
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 403


def test_profilo_doppio_rifiutato(client, bagnino):
    r = client.post(
        "/bagnini",
        json={"nome": "Altro", "cognome": "Profilo"},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 409


def test_endpoint_me_senza_profilo(client):
    registra(client, "senzaprofilo@test.it", "bagnino")
    token = login(client, "senzaprofilo@test.it")
    r = client.get("/bagnini/me", headers=auth(token))
    assert r.status_code == 409  # deve prima creare il profilo


def test_modifica_parziale_non_azzera_gli_altri_campi(client, bagnino):
    r = client.patch(
        "/bagnini/me", json={"anni_esperienza": 9}, headers=auth(bagnino["token"])
    )
    assert r.status_code == 200
    assert r.json()["anni_esperienza"] == 9
    assert r.json()["nome"] == "Marco"  # invariato


def test_eta_calcolata_da_data_nascita(client, bagnino):
    r = client.patch(
        "/bagnini/me", json={"data_nascita": "1990-01-01"}, headers=auth(bagnino["token"])
    )
    assert r.json()["eta"] >= 35


def test_brevetto_scaduto_rende_non_abilitato(client):
    registra(client, "scaduto@test.it", "bagnino")
    token = login(client, "scaduto@test.it")
    client.post("/bagnini", json={"nome": "Vec", "cognome": "Chio"}, headers=auth(token))
    r = client.post(
        "/bagnini/me/brevetti",
        json={"tipo": "P", "data_scadenza": "2020-01-01"},
        headers=auth(token),
    )
    assert r.status_code == 201
    assert r.json()["valido"] is False
    assert client.get("/bagnini/me", headers=auth(token)).json()["abilitato"] is False


def test_filtro_solo_abilitati(client, bagnino):
    # Un secondo bagnino senza brevetti: non deve comparire fra gli abilitati.
    registra(client, "nobrevetto@test.it", "bagnino")
    token = login(client, "nobrevetto@test.it")
    client.post("/bagnini", json={"nome": "Sen", "cognome": "Za"}, headers=auth(token))

    assert client.get("/bagnini").json()["totale"] == 2
    solo_abilitati = client.get("/bagnini", params={"solo_abilitati": True}).json()
    assert solo_abilitati["totale"] == 1
    assert solo_abilitati["elementi"][0]["nome"] == "Marco"


def test_filtro_per_zona(client, bagnino):
    assert client.get("/bagnini", params={"zona_id": 1}).json()["totale"] == 1
    assert client.get("/bagnini", params={"zona_id": 2}).json()["totale"] == 0


def test_non_si_cancella_il_brevetto_di_un_altro(client, bagnino):
    registra(client, "ladro@test.it", "bagnino")
    token_ladro = login(client, "ladro@test.it")
    client.post("/bagnini", json={"nome": "La", "cognome": "Dro"}, headers=auth(token_ladro))

    r = client.delete("/bagnini/me/brevetti/1", headers=auth(token_ladro))
    assert r.status_code == 404  # il brevetto 1 è del primo bagnino
    assert client.get("/bagnini/me", headers=auth(bagnino["token"])).json()["abilitato"] is True


def test_piscina_profilo_e_ricerca(client, piscina):
    r = client.get("/piscine/me", headers=auth(piscina["token"]))
    assert r.json()["nome_struttura"] == "Aqua Test"

    assert client.get("/piscine", params={"tipo_struttura": "hotel"}).json()["totale"] == 1
    assert client.get("/piscine", params={"tipo_struttura": "comunale"}).json()["totale"] == 0
