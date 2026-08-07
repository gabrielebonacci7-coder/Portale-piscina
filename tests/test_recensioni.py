"""Regole sulle recensioni: chi può recensire chi, quando e con quali voti."""

from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import auth


def fra_giorni(n: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=n)).isoformat()


@pytest.fixture
def turno_concluso(client, piscina, bagnino):
    """Un annuncio assegnato al bagnino e poi chiuso."""
    annuncio_id = client.post(
        "/annunci",
        json={
            "titolo": "Turno svolto",
            "tipo": "piscina_cerca_bagnino",
            "data_inizio": fra_giorni(1),
            "compenso": "13.00",
        },
        headers=auth(piscina["token"]),
    ).json()["id"]

    client.post(
        f"/annunci/{annuncio_id}/assegna",
        params={"assegnatario_id": bagnino["utente_id"]},
        headers=auth(piscina["token"]),
    )
    client.post(f"/annunci/{annuncio_id}/chiudi", headers=auth(piscina["token"]))
    return annuncio_id


def test_piscina_recensisce_il_bagnino(client, piscina, bagnino, turno_concluso):
    r = client.post(
        "/recensioni",
        json={
            "destinatario_id": bagnino["utente_id"],
            "annuncio_id": turno_concluso,
            "stelle": 5,
            "commento": "Ottimo lavoro",
            "voto_puntualita": 5,
            "voto_professionalita": 4,
        },
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 201, r.text
    assert r.json()["autore_nome"] == "Aqua Test"


def test_bagnino_recensisce_la_piscina(client, piscina, bagnino, turno_concluso):
    r = client.post(
        "/recensioni",
        json={
            "destinatario_id": piscina["utente_id"],
            "annuncio_id": turno_concluso,
            "stelle": 4,
            "voto_ambiente": 5,
            "voto_pagamento": 4,
        },
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 201, r.text
    assert r.json()["autore_nome"] == "Marco Rossi"


def test_voti_nel_verso_sbagliato_rifiutati(client, piscina, bagnino, turno_concluso):
    # Una piscina non vota "pagamento puntuale": è il bagnino a farlo.
    r = client.post(
        "/recensioni",
        json={
            "destinatario_id": bagnino["utente_id"],
            "annuncio_id": turno_concluso,
            "stelle": 5,
            "voto_pagamento": 5,
        },
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 422
    assert "voto_pagamento" in r.json()["detail"]


def test_niente_recensione_se_il_turno_non_e_concluso(client, piscina, bagnino):
    annuncio_id = client.post(
        "/annunci",
        json={
            "titolo": "Ancora aperto",
            "tipo": "piscina_cerca_bagnino",
            "data_inizio": fra_giorni(2),
        },
        headers=auth(piscina["token"]),
    ).json()["id"]

    r = client.post(
        "/recensioni",
        json={"destinatario_id": bagnino["utente_id"], "annuncio_id": annuncio_id, "stelle": 5},
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 409


def test_estraneo_non_puo_recensire(client, piscina, bagnino, turno_concluso):
    from tests.conftest import login, registra

    registra(client, "estraneo@test.it", "bagnino")
    token = login(client, "estraneo@test.it")
    client.post("/bagnini", json={"nome": "Es", "cognome": "Traneo"}, headers=auth(token))

    r = client.post(
        "/recensioni",
        json={"destinatario_id": piscina["utente_id"], "annuncio_id": turno_concluso, "stelle": 1},
        headers=auth(token),
    )
    assert r.status_code == 403


def test_recensione_doppia_rifiutata(client, piscina, bagnino, turno_concluso):
    corpo = {
        "destinatario_id": bagnino["utente_id"],
        "annuncio_id": turno_concluso,
        "stelle": 5,
    }
    assert client.post("/recensioni", json=corpo, headers=auth(piscina["token"])).status_code == 201
    assert client.post("/recensioni", json=corpo, headers=auth(piscina["token"])).status_code == 409


def test_autorecensione_rifiutata(client, piscina, turno_concluso):
    r = client.post(
        "/recensioni",
        json={"destinatario_id": piscina["utente_id"], "annuncio_id": turno_concluso, "stelle": 5},
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 422


def test_stelle_fuori_scala_rifiutate(client, piscina, bagnino, turno_concluso):
    r = client.post(
        "/recensioni",
        json={"destinatario_id": bagnino["utente_id"], "annuncio_id": turno_concluso, "stelle": 9},
        headers=auth(piscina["token"]),
    )
    assert r.status_code == 422


def test_riepilogo_con_medie(client, piscina, bagnino, turno_concluso):
    client.post(
        "/recensioni",
        json={
            "destinatario_id": bagnino["utente_id"],
            "annuncio_id": turno_concluso,
            "stelle": 4,
            "voto_puntualita": 5,
        },
        headers=auth(piscina["token"]),
    )

    r = client.get(
        f"/utenti/{bagnino['utente_id']}/recensioni", headers=auth(piscina["token"])
    )
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["totale"] == 1
    assert corpo["media_stelle"] == 4.0
    assert corpo["media_puntualita"] == 5.0
    assert corpo["media_pagamento"] is None  # nessuno l'ha votato
