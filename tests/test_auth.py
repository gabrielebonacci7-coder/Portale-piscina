"""Registrazione, login e protezione degli endpoint."""

from tests.conftest import auth, login, registra


def test_registrazione_e_login(client):
    utente = registra(client, "nuovo@test.it", "bagnino")
    assert utente["email"] == "nuovo@test.it"
    assert "password" not in utente and "password_hash" not in utente

    token = login(client, "nuovo@test.it")
    r = client.get("/auth/me", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["email"] == "nuovo@test.it"


def test_email_duplicata_rifiutata(client):
    registra(client, "doppio@test.it", "bagnino")
    r = client.post(
        "/auth/registrazione",
        json={"email": "doppio@test.it", "password": "password123", "tipo": "piscina"},
    )
    assert r.status_code == 409


def test_email_normalizzata_in_minuscolo(client):
    registra(client, "Mixed@Test.it", "bagnino")
    # Il login funziona comunque, con qualsiasi combinazione di maiuscole.
    assert login(client, "mixed@test.it")
    assert login(client, "MIXED@TEST.IT")


def test_password_sbagliata_rifiutata(client):
    registra(client, "tizio@test.it", "bagnino")
    r = client.post("/auth/login", json={"email": "tizio@test.it", "password": "sbagliata"})
    assert r.status_code == 401


def test_password_corta_rifiutata(client):
    r = client.post(
        "/auth/registrazione",
        json={"email": "corta@test.it", "password": "1234", "tipo": "bagnino"},
    )
    assert r.status_code == 422


def test_endpoint_protetto_senza_token(client):
    assert client.get("/auth/me").status_code == 401


def test_token_non_valido_rifiutato(client):
    assert client.get("/auth/me", headers=auth("token-inventato")).status_code == 401


def test_cambio_password(client):
    registra(client, "cambio@test.it", "bagnino")
    token = login(client, "cambio@test.it")

    r = client.post(
        "/auth/cambio-password",
        json={"password_attuale": "sbagliata", "password_nuova": "nuovapassword"},
        headers=auth(token),
    )
    assert r.status_code == 400

    r = client.post(
        "/auth/cambio-password",
        json={"password_attuale": "password123", "password_nuova": "nuovapassword"},
        headers=auth(token),
    )
    assert r.status_code == 204
    assert login(client, "cambio@test.it", "nuovapassword")
