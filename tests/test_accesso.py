"""La bacheca è riservata agli iscritti: senza token si vede solo l'anagrafica zone."""

import pytest

from tests.conftest import auth

RISERVATI = [
    "/annunci",
    "/annunci/1",
    "/annunci/miei",
    "/bagnini",
    "/bagnini/1",
    "/bagnini/me",
    "/piscine",
    "/piscine/1",
    "/piscine/me",
    "/utenti/1/recensioni",
    "/conversazioni",
    "/candidature/mie",
    "/blocchi",
]


@pytest.mark.parametrize("percorso", RISERVATI)
def test_senza_token_si_viene_respinti(client, percorso):
    assert client.get(percorso).status_code == 401


def test_le_zone_restano_pubbliche(client):
    """Servono al modulo di registrazione, prima che l'account esista."""
    r = client.get("/zone")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_con_token_la_bacheca_si_apre(client, piscina):
    assert client.get("/annunci", headers=auth(piscina["token"])).status_code == 200
    assert client.get("/bagnini", headers=auth(piscina["token"])).status_code == 200
