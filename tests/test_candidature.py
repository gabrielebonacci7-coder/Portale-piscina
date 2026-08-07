"""Candidature: chi può candidarsi, il brevetto richiesto, accettazione e ritiro."""

from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import auth, login, registra


def fra_giorni(n: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=n)).isoformat()


def pubblica(client, token: str, **extra):
    dati = {
        "titolo": "Turno pomeridiano",
        "tipo": "piscina_cerca_bagnino",
        "data_inizio": fra_giorni(3),
        "compenso": "13.00",
    }
    dati.update(extra)
    r = client.post("/annunci", json=dati, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def crea_bagnino(client, email: str, brevetto: str | None = "MIP", scadenza: str = "2030-01-01"):
    """Secondo bagnino, con brevetto configurabile. Restituisce (token, utente_id)."""
    utente = registra(client, email, "bagnino")
    token = login(client, email)
    client.post("/bagnini", json={"nome": "Test", "cognome": email[:3]}, headers=auth(token))
    if brevetto:
        client.post(
            "/bagnini/me/brevetti",
            json={"tipo": brevetto, "data_scadenza": scadenza},
            headers=auth(token),
        )
    return token, utente["id"]


@pytest.fixture
def annuncio(client, piscina):
    return pubblica(client, piscina["token"])


def test_bagnino_si_candida(client, piscina, bagnino, annuncio):
    r = client.post(
        f"/annunci/{annuncio}/candidature",
        json={"messaggio": "Disponibile, abito in zona"},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 201, r.text
    assert r.json()["stato"] == "inviata"
    assert r.json()["candidato"]["nome_visualizzato"] == "Marco Rossi"


def test_la_piscina_vede_le_candidature_il_bagnino_no(client, piscina, bagnino, annuncio):
    client.post(f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"]))

    r = client.get(f"/annunci/{annuncio}/candidature", headers=auth(piscina["token"]))
    assert r.status_code == 200 and r.json()["totale"] == 1

    # Un candidato non può sbirciare chi altro si è proposto.
    r = client.get(f"/annunci/{annuncio}/candidature", headers=auth(bagnino["token"]))
    assert r.status_code == 403


def test_non_ci_si_candida_al_proprio_annuncio(client, piscina, annuncio):
    r = client.post(f"/annunci/{annuncio}/candidature", json={}, headers=auth(piscina["token"]))
    assert r.status_code == 422


def test_solo_la_controparte_puo_candidarsi(client, piscina, annuncio):
    # Un'altra piscina non risponde a "piscina cerca bagnino".
    registra(client, "altra@test.it", "piscina")
    token = login(client, "altra@test.it")
    client.post("/piscine", json={"nome_struttura": "Altra"}, headers=auth(token))

    r = client.post(f"/annunci/{annuncio}/candidature", json={}, headers=auth(token))
    assert r.status_code == 422


def test_candidatura_doppia_rifiutata(client, bagnino, annuncio):
    assert client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"])
    ).status_code == 201
    r = client.post(f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"]))
    assert r.status_code == 409


def test_niente_candidature_su_turni_passati(client, piscina, bagnino):
    passato = pubblica(client, piscina["token"], data_inizio=fra_giorni(-1))
    r = client.post(f"/annunci/{passato}/candidature", json={}, headers=auth(bagnino["token"]))
    assert r.status_code == 409


def test_brevetto_richiesto_blocca_chi_non_ce_l_ha(client, piscina):
    turno = pubblica(client, piscina["token"], brevetto_richiesto="MIP")

    # Ha solo il brevetto P: non copre un turno che richiede MIP.
    token, _ = crea_bagnino(client, "solop@test.it", brevetto="P")
    r = client.post(f"/annunci/{turno}/candidature", json={}, headers=auth(token))
    assert r.status_code == 403
    assert "MIP" in r.json()["detail"]


def test_brevetto_superiore_copre_quello_richiesto(client, piscina):
    turno = pubblica(client, piscina["token"], brevetto_richiesto="P")

    # MIP contiene P: la candidatura passa.
    token, _ = crea_bagnino(client, "mip@test.it", brevetto="MIP")
    assert client.post(
        f"/annunci/{turno}/candidature", json={}, headers=auth(token)
    ).status_code == 201


def test_brevetto_scaduto_non_vale(client, piscina):
    turno = pubblica(client, piscina["token"], brevetto_richiesto="P")

    token, _ = crea_bagnino(client, "scaduto@test.it", brevetto="MIP", scadenza="2020-01-01")
    r = client.post(f"/annunci/{turno}/candidature", json={}, headers=auth(token))
    assert r.status_code == 403


def test_senza_brevetto_richiesto_si_candidano_tutti(client, piscina, annuncio):
    token, _ = crea_bagnino(client, "nessuno@test.it", brevetto=None)
    assert client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(token)
    ).status_code == 201


def test_accettare_assegna_il_turno_e_rifiuta_gli_altri(client, piscina, bagnino, annuncio):
    prima = client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"])
    ).json()
    token2, utente2 = crea_bagnino(client, "secondo@test.it")
    seconda = client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(token2)
    ).json()

    r = client.post(
        f"/annunci/{annuncio}/candidature/{prima['id']}/accetta", headers=auth(piscina["token"])
    )
    assert r.status_code == 200 and r.json()["stato"] == "accettata"

    # L'annuncio risulta assegnato al candidato scelto.
    dettaglio = client.get(f"/annunci/{annuncio}", headers=auth(piscina["token"])).json()
    assert dettaglio["stato"] == "assegnato"
    assert dettaglio["assegnato_a_id"] == bagnino["utente_id"]

    # L'altra candidatura è stata rifiutata automaticamente.
    elenco = client.get(f"/annunci/{annuncio}/candidature", headers=auth(piscina["token"])).json()
    stati = {c["id"]: c["stato"] for c in elenco["elementi"]}
    assert stati[seconda["id"]] == "rifiutata"


def test_non_ci_si_candida_a_un_annuncio_gia_assegnato(client, piscina, bagnino, annuncio):
    prima = client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"])
    ).json()
    client.post(
        f"/annunci/{annuncio}/candidature/{prima['id']}/accetta", headers=auth(piscina["token"])
    )

    token2, _ = crea_bagnino(client, "tardivo@test.it")
    r = client.post(f"/annunci/{annuncio}/candidature", json={}, headers=auth(token2))
    assert r.status_code == 409


def test_solo_l_autore_accetta_o_rifiuta(client, piscina, bagnino, annuncio):
    c = client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"])
    ).json()

    # Il candidato non può accettarsi da solo.
    r = client.post(
        f"/annunci/{annuncio}/candidature/{c['id']}/accetta", headers=auth(bagnino["token"])
    )
    assert r.status_code == 403


def test_rifiuto_esplicito(client, piscina, bagnino, annuncio):
    c = client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"])
    ).json()
    r = client.post(
        f"/annunci/{annuncio}/candidature/{c['id']}/rifiuta", headers=auth(piscina["token"])
    )
    assert r.status_code == 200 and r.json()["stato"] == "rifiutata"
    # L'annuncio resta aperto per altri.
    assert client.get(
        f"/annunci/{annuncio}", headers=auth(piscina["token"])
    ).json()["stato"] == "aperto"


def test_ritiro_candidatura(client, piscina, bagnino, annuncio):
    c = client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"])
    ).json()

    r = client.delete(f"/candidature/{c['id']}", headers=auth(bagnino["token"]))
    assert r.status_code == 200 and r.json()["stato"] == "ritirata"

    # Ritirata una volta, non si ritira di nuovo.
    assert client.delete(f"/candidature/{c['id']}", headers=auth(bagnino["token"])).status_code == 409


def test_non_si_ritira_la_candidatura_di_un_altro(client, piscina, bagnino, annuncio):
    c = client.post(
        f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"])
    ).json()
    token2, _ = crea_bagnino(client, "estraneo2@test.it")
    assert client.delete(f"/candidature/{c['id']}", headers=auth(token2)).status_code == 404


def test_mie_candidature(client, piscina, bagnino, annuncio):
    client.post(f"/annunci/{annuncio}/candidature", json={}, headers=auth(bagnino["token"]))

    r = client.get("/candidature/mie", headers=auth(bagnino["token"]))
    assert r.status_code == 200
    assert r.json()["totale"] == 1
    voce = r.json()["elementi"][0]
    assert voce["annuncio_titolo"] == "Turno pomeridiano"
    assert voce["annuncio_data_inizio"] is not None


def test_bagnino_cerca_sostituzione_riceve_candidature_dalle_piscine(client, piscina, bagnino):
    turno = pubblica(
        client, bagnino["token"], tipo="bagnino_cerca_sostituzione", titolo="Cerco chi mi copre"
    )
    r = client.post(f"/annunci/{turno}/candidature", json={}, headers=auth(piscina["token"]))
    assert r.status_code == 201, r.text
