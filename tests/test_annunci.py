"""Pubblicazione, ricerca in bacheca, proprietà e assegnazione degli annunci."""

from datetime import datetime, timedelta, timezone

from tests.conftest import auth, login, registra


def fra_giorni(n: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=n)).isoformat()


def annuncio_base(**extra) -> dict:
    dati = {
        "titolo": "Turno pomeridiano",
        "tipo": "piscina_cerca_bagnino",
        "data_inizio": fra_giorni(3),
        "compenso": "13.00",
        "tipo_turno": "turno_fisso",
        "zona_id": 1,
    }
    dati.update(extra)
    return dati


def pubblica(client, token: str, **extra):
    return client.post("/annunci", json=annuncio_base(**extra), headers=auth(token))


def test_piscina_pubblica_annuncio(client, piscina):
    r = pubblica(client, piscina["token"])
    assert r.status_code == 201, r.text
    corpo = r.json()
    assert corpo["autore_id"] == piscina["utente_id"]
    # La piscina di riferimento viene compilata da sola.
    assert corpo["piscina_id"] == piscina["profilo_id"]
    assert corpo["autore"]["nome_visualizzato"] == "Aqua Test"
    assert corpo["stato"] == "aperto"


def test_tipo_annuncio_deve_corrispondere_al_tipo_account(client, piscina, bagnino):
    # Una piscina non può dire "bagnino cerca sostituzione".
    r = pubblica(client, piscina["token"], tipo="bagnino_cerca_sostituzione")
    assert r.status_code == 422
    # E un bagnino non può dire "piscina cerca bagnino".
    r = pubblica(client, bagnino["token"], tipo="piscina_cerca_bagnino")
    assert r.status_code == 422
    # Ciascuno nel proprio verso funziona.
    assert pubblica(client, bagnino["token"], tipo="bagnino_cerca_sostituzione").status_code == 201


def test_senza_profilo_non_si_pubblica(client):
    registra(client, "vuoto@test.it", "piscina")
    token = login(client, "vuoto@test.it")
    assert pubblica(client, token).status_code == 409


def test_data_fine_prima_di_inizio_rifiutata(client, piscina):
    r = pubblica(client, piscina["token"], data_fine=fra_giorni(1))
    assert r.status_code == 422


def test_bacheca_nasconde_i_turni_passati(client, piscina):
    pubblica(client, piscina["token"], titolo="Futuro")
    pubblica(client, piscina["token"], titolo="Passato", data_inizio=fra_giorni(-5))

    aperti = client.get("/annunci", headers=auth(piscina["token"])).json()
    assert [a["titolo"] for a in aperti["elementi"]] == ["Futuro"]

    tutti = client.get(
        "/annunci", params={"solo_aperti": False}, headers=auth(piscina["token"])
    ).json()
    assert tutti["totale"] == 2


def test_urgenti_in_cima(client, piscina):
    pubblica(client, piscina["token"], titolo="Normale", data_inizio=fra_giorni(1))
    pubblica(client, piscina["token"], titolo="Urgente", data_inizio=fra_giorni(9), urgente=True)

    bacheca = client.get("/annunci", headers=auth(piscina["token"])).json()
    titoli = [a["titolo"] for a in bacheca["elementi"]]
    assert titoli == ["Urgente", "Normale"]


def test_filtri_bacheca(client, piscina):
    pubblica(client, piscina["token"], titolo="Serale EUR", tipo_turno="evento_serale", zona_id=1)
    pubblica(client, piscina["token"], titolo="Fisso Ostia", tipo_turno="turno_fisso", zona_id=2)

    def totale(**params):
        return client.get(
            "/annunci", params=params, headers=auth(piscina["token"])
        ).json()["totale"]

    assert totale(zona_id=1) == 1
    assert totale(tipo_turno="evento_serale") == 1
    assert totale(compenso_min=20) == 0
    assert totale(compenso_min=10) == 2
    assert totale(testo="Ostia") == 1
    assert totale(data_da=fra_giorni(10)) == 0


def test_paginazione(client, piscina):
    for i in range(5):
        pubblica(client, piscina["token"], titolo=f"Turno {i}", data_inizio=fra_giorni(i + 1))

    pagina = client.get(
        "/annunci", params={"skip": 2, "limit": 2}, headers=auth(piscina["token"])
    ).json()
    assert pagina["totale"] == 5  # il totale è quello complessivo
    assert len(pagina["elementi"]) == 2
    assert [a["titolo"] for a in pagina["elementi"]] == ["Turno 2", "Turno 3"]


def test_solo_l_autore_modifica_ed_elimina(client, piscina, bagnino):
    annuncio_id = pubblica(client, piscina["token"]).json()["id"]

    r = client.patch(
        f"/annunci/{annuncio_id}", json={"titolo": "Rubato"}, headers=auth(bagnino["token"])
    )
    assert r.status_code == 403
    assert client.delete(f"/annunci/{annuncio_id}", headers=auth(bagnino["token"])).status_code == 403

    r = client.patch(
        f"/annunci/{annuncio_id}", json={"titolo": "Corretto"}, headers=auth(piscina["token"])
    )
    assert r.status_code == 200 and r.json()["titolo"] == "Corretto"
    assert client.delete(f"/annunci/{annuncio_id}", headers=auth(piscina["token"])).status_code == 204
    assert client.get(
        f"/annunci/{annuncio_id}", headers=auth(piscina["token"])
    ).status_code == 404


def test_assegnazione(client, piscina, bagnino):
    annuncio_id = pubblica(client, piscina["token"]).json()["id"]

    r = client.post(
        f"/annunci/{annuncio_id}/assegna",
        params={"assegnatario_id": bagnino["utente_id"]},
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 200
    assert r.json()["stato"] == "assegnato"
    assert r.json()["assegnato_a_id"] == bagnino["utente_id"]

    # Un annuncio già assegnato non si riassegna.
    r = client.post(
        f"/annunci/{annuncio_id}/assegna",
        params={"assegnatario_id": bagnino["utente_id"]},
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 409


def test_non_si_assegna_a_un_account_dello_stesso_tipo(client, piscina):
    registra(client, "altrapiscina@test.it", "piscina")
    altra = client.post("/auth/login", json={"email": "altrapiscina@test.it", "password": "password123"})
    altra_id = altra.json()["utente"]["id"]

    annuncio_id = pubblica(client, piscina["token"]).json()["id"]
    r = client.post(
        f"/annunci/{annuncio_id}/assegna",
        params={"assegnatario_id": altra_id},
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 422


def test_miei_annunci_mostra_anche_i_chiusi(client, piscina, bagnino):
    pubblica(client, piscina["token"], titolo="Passato", data_inizio=fra_giorni(-2))
    pubblica(client, piscina["token"], titolo="Futuro")

    miei = client.get("/annunci/miei", headers=auth(piscina["token"])).json()
    assert miei["totale"] == 2
    # Il bagnino non vede gli annunci altrui in "miei".
    assert client.get("/annunci/miei", headers=auth(bagnino["token"])).json()["totale"] == 0
