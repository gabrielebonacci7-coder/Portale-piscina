"""Chat interna: conversazioni, non letti, chat fra bagnini, blocco."""

import pytest

from tests.conftest import auth, login, registra


@pytest.fixture
def secondo_bagnino(client):
    """Un collega, per provare la chat bagnino-bagnino."""
    utente = registra(client, "collega@test.it", "bagnino")
    token = login(client, "collega@test.it")
    client.post("/bagnini", json={"nome": "Luca", "cognome": "Verdi"}, headers=auth(token))
    return {"token": token, "utente_id": utente["id"]}


def scrivi(client, token, destinatario_id, testo, **extra):
    return client.post(
        "/conversazioni",
        json={"destinatario_id": destinatario_id, "testo": testo, **extra},
        headers=auth(token),
    )


def test_piscina_scrive_a_bagnino(client, piscina, bagnino):
    r = scrivi(client, piscina["token"], bagnino["utente_id"], "Buongiorno, è ancora disponibile?")
    assert r.status_code == 201, r.text
    assert r.json()["testo"] == "Buongiorno, è ancora disponibile?"
    assert r.json()["mittente_id"] == piscina["utente_id"]


def test_bagnino_scrive_a_bagnino(client, bagnino, secondo_bagnino):
    """Fra colleghi ci si scambia i turni: la chat non è solo verso le strutture."""
    r = scrivi(client, bagnino["token"], secondo_bagnino["utente_id"], "Mi copri sabato?")
    assert r.status_code == 201, r.text


def test_la_conversazione_e_una_sola_fra_due_persone(client, piscina, bagnino):
    prima = scrivi(client, piscina["token"], bagnino["utente_id"], "Primo").json()
    # Anche scrivendo di nuovo, o rispondendo, la conversazione resta quella.
    seconda = scrivi(client, piscina["token"], bagnino["utente_id"], "Secondo").json()
    terza = scrivi(client, bagnino["token"], piscina["utente_id"], "Rispondo").json()

    assert prima["conversazione_id"] == seconda["conversazione_id"] == terza["conversazione_id"]
    assert client.get("/conversazioni", headers=auth(piscina["token"])).json()["totale"] == 1


def test_elenco_mostra_interlocutore_e_ultimo_messaggio(client, piscina, bagnino):
    scrivi(client, piscina["token"], bagnino["utente_id"], "Ciao")
    scrivi(client, bagnino["token"], piscina["utente_id"], "Eccomi")

    r = client.get("/conversazioni", headers=auth(piscina["token"])).json()
    conv = r["elementi"][0]
    assert conv["interlocutore"]["nome_visualizzato"] == "Marco Rossi"
    assert conv["ultimo_messaggio"] == "Eccomi"


def test_conteggio_non_letti(client, piscina, bagnino):
    scrivi(client, piscina["token"], bagnino["utente_id"], "Uno")
    scrivi(client, piscina["token"], bagnino["utente_id"], "Due")

    # Chi ha scritto non ha nulla da leggere.
    mittente = client.get("/conversazioni", headers=auth(piscina["token"])).json()
    assert mittente["elementi"][0]["non_letti"] == 0

    # Il destinatario sì.
    destinatario = client.get("/conversazioni", headers=auth(bagnino["token"])).json()
    conv_id = destinatario["elementi"][0]["id"]
    assert destinatario["elementi"][0]["non_letti"] == 2
    assert client.get("/conversazioni/non-letti", headers=auth(bagnino["token"])).json()[
        "non_letti"
    ] == 2

    # Aprire i messaggi li segna come letti.
    r = client.get(f"/conversazioni/{conv_id}/messaggi", headers=auth(bagnino["token"]))
    assert r.status_code == 200 and r.json()["totale"] == 2
    dopo = client.get("/conversazioni", headers=auth(bagnino["token"])).json()
    assert dopo["elementi"][0]["non_letti"] == 0


def test_messaggi_in_ordine_cronologico(client, piscina, bagnino):
    conv_id = scrivi(client, piscina["token"], bagnino["utente_id"], "Primo").json()[
        "conversazione_id"
    ]
    client.post(
        f"/conversazioni/{conv_id}/messaggi",
        json={"testo": "Secondo"},
        headers=auth(bagnino["token"]),
    )
    r = client.get(f"/conversazioni/{conv_id}/messaggi", headers=auth(piscina["token"])).json()
    assert [m["testo"] for m in r["elementi"]] == ["Primo", "Secondo"]


def test_estraneo_non_vede_la_conversazione(client, piscina, bagnino, secondo_bagnino):
    conv_id = scrivi(client, piscina["token"], bagnino["utente_id"], "Riservato").json()[
        "conversazione_id"
    ]
    # 404 e non 403: chi non partecipa non deve sapere che esiste.
    r = client.get(f"/conversazioni/{conv_id}/messaggi", headers=auth(secondo_bagnino["token"]))
    assert r.status_code == 404
    r = client.post(
        f"/conversazioni/{conv_id}/messaggi",
        json={"testo": "Mi intrufolo"},
        headers=auth(secondo_bagnino["token"]),
    )
    assert r.status_code == 404


def test_non_si_scrive_a_se_stessi(client, piscina):
    assert scrivi(client, piscina["token"], piscina["utente_id"], "Ciao me").status_code == 422


def test_messaggio_vuoto_rifiutato(client, piscina, bagnino):
    assert scrivi(client, piscina["token"], bagnino["utente_id"], "   ").status_code == 422
    assert scrivi(client, piscina["token"], bagnino["utente_id"], "").status_code == 422


def test_senza_profilo_non_si_scrive(client, bagnino):
    registra(client, "nudo@test.it", "piscina")
    token = login(client, "nudo@test.it")
    assert scrivi(client, token, bagnino["utente_id"], "Ciao").status_code == 409


def test_serve_il_login(client, bagnino):
    r = client.post(
        "/conversazioni", json={"destinatario_id": bagnino["utente_id"], "testo": "Ciao"}
    )
    assert r.status_code == 401


# --- Blocchi --------------------------------------------------------------
def test_blocco_impedisce_di_scrivere_in_entrambi_i_versi(client, piscina, bagnino):
    conv_id = scrivi(client, piscina["token"], bagnino["utente_id"], "Ciao").json()[
        "conversazione_id"
    ]

    r = client.post(
        f"/blocchi/{piscina['utente_id']}",
        json={"motivo": "messaggi insistenti"},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 201

    # Chi è stato bloccato non può più scrivere...
    r = client.post(
        f"/conversazioni/{conv_id}/messaggi",
        json={"testo": "Ci sei?"},
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 403

    # ...e nemmeno chi ha bloccato, finché non sblocca.
    r = client.post(
        f"/conversazioni/{conv_id}/messaggi",
        json={"testo": "Ripensandoci"},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 403


def test_blocco_impedisce_anche_di_aprire_una_nuova_conversazione(client, piscina, bagnino):
    client.post(f"/blocchi/{piscina['utente_id']}", json={}, headers=auth(bagnino["token"]))
    assert scrivi(client, piscina["token"], bagnino["utente_id"], "Ciao").status_code == 403


def test_sblocco(client, piscina, bagnino):
    client.post(f"/blocchi/{piscina['utente_id']}", json={}, headers=auth(bagnino["token"]))
    assert scrivi(client, piscina["token"], bagnino["utente_id"], "Ciao").status_code == 403

    r = client.delete(f"/blocchi/{piscina['utente_id']}", headers=auth(bagnino["token"]))
    assert r.status_code == 204
    assert scrivi(client, piscina["token"], bagnino["utente_id"], "Ciao").status_code == 201


def test_elenco_blocchi(client, piscina, bagnino):
    client.post(
        f"/blocchi/{piscina['utente_id']}", json={"motivo": "spam"}, headers=auth(bagnino["token"])
    )
    r = client.get("/blocchi", headers=auth(bagnino["token"]))
    assert r.status_code == 200
    assert r.json()[0]["bloccato_id"] == piscina["utente_id"]
    assert r.json()[0]["motivo"] == "spam"


def test_non_ci_si_blocca_da_soli(client, piscina):
    assert client.post(
        f"/blocchi/{piscina['utente_id']}", json={}, headers=auth(piscina["token"])
    ).status_code == 422


def test_blocco_ripetuto_non_duplica(client, piscina, bagnino):
    primo = client.post(
        f"/blocchi/{piscina['utente_id']}", json={}, headers=auth(bagnino["token"])
    ).json()
    secondo = client.post(
        f"/blocchi/{piscina['utente_id']}", json={}, headers=auth(bagnino["token"])
    ).json()
    assert primo["id"] == secondo["id"]
    assert len(client.get("/blocchi", headers=auth(bagnino["token"])).json()) == 1


def test_sbloccare_chi_non_e_bloccato(client, piscina, bagnino):
    r = client.delete(f"/blocchi/{piscina['utente_id']}", headers=auth(bagnino["token"]))
    assert r.status_code == 404
