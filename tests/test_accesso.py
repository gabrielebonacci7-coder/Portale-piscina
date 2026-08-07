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


def test_zone_raggruppate_per_area(client):
    """Le zone arrivano già ordinate: Roma per prima, poi le altre aree."""
    zone = client.get("/zone").json()
    aree = [z["area"] for z in zone]
    assert aree == sorted(aree, key=lambda a: 0 if a == "Roma" else 1)
    assert set(aree) >= {"Roma"}


def test_filtro_per_area(client, db_engine):
    """Il filtro `area` serve alla PWA per costruire i menù a gruppi."""
    from sqlalchemy.orm import sessionmaker

    from app.models import Zona

    with sessionmaker(bind=db_engine)() as db:
        db.add(Zona(nome="Frascati", citta="Frascati", area="Castelli Romani"))
        db.commit()

    castelli = client.get("/zone", params={"area": "Castelli Romani"}).json()
    assert [z["nome"] for z in castelli] == ["Frascati"]
    assert castelli[0]["citta"] == "Frascati"  # non "Roma": è un comune a sé

    romane = client.get("/zone", params={"area": "Roma"}).json()
    assert all(z["citta"] == "Roma" for z in romane)
