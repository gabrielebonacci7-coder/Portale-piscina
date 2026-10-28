"""Ambiente delle prove: database in una cartella temporanea, orologio fermo.

L'orologio è fermo a **lunedì 12 ottobre 2026, ore 9:00 a Roma**. Così le
regole di tempo si provano senza dipendere dal giorno in cui si lanciano i
test: la lezione delle 16:30 di oggi è fra 7 ore e mezza (non si può più
disdire), quella di domani sì.
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_cartella = tempfile.mkdtemp(prefix="reformer-test-")
os.environ["REFORMER_DATABASE_URL"] = f"sqlite:///{Path(_cartella) / 'test.db'}"
os.environ["REFORMER_BCRYPT_ROUNDS"] = "4"
os.environ["REFORMER_PROMEMORIA_ATTIVI"] = "false"
os.environ["REFORMER_EMAIL_SMTP_HOST"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from reformer.core import email as posta  # noqa: E402
from reformer.core import limiti  # noqa: E402
from reformer.db.base import Base  # noqa: E402
from reformer.db.session import engine  # noqa: E402
from reformer.dominio import orario  # noqa: E402
from reformer.main import app  # noqa: E402

LUNEDI_9 = datetime(2026, 10, 12, 7, 0, tzinfo=timezone.utc)  # le 9:00 a Roma

GRETA = "greta.lorenzetti@icloud.com"
ELISA = "elisabonacci@yahoo.it"


class Orologio:
    def __init__(self):
        self.ora = LUNEDI_9

    def avanti(self, **kw):
        self.ora += timedelta(**kw)


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    limiti.azzera_tutto()
    orologio = Orologio()
    monkeypatch.setattr(orario, "adesso", lambda: orologio.ora)
    monkeypatch.setattr(orario, "oggi", lambda: orologio.ora.astimezone(orario.FUSO).date())
    yield orologio


@pytest.fixture
def orologio(ambiente):
    return ambiente


@pytest.fixture
def posta_inviata(monkeypatch):
    """Le email che partirebbero: (destinatario, oggetto, testo)."""
    inviate = []
    monkeypatch.setattr(posta, "invia_email", lambda a, o, t: inviate.append((a, o, t)))
    return inviate


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def registra(client, email, nome="Sofia", cognome="Marini", password="pilates2026", lezioni=10):
    """Registra una cliente e le carica `lezioni` nel pacchetto (come farebbe
    lo studio dopo il pagamento): senza lezioni non si prenota."""
    r = client.post("/api/auth/registrati", json={
        "nome": nome, "cognome": cognome, "telefono": "333 1234567",
        "email": email, "password": password, "privacy": True,
    })
    assert r.status_code == 201, r.text
    if lezioni:
        from reformer.db.session import SessionLocal
        from reformer.models import Utente

        with SessionLocal() as db:
            u = db.get(Utente, r.json()["utente"]["id"])
            u.lezioni_rimaste = lezioni
            db.commit()
    return r.json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def codice_dal_link(testo: str) -> str:
    riga = next(r for r in testo.splitlines() if "/#/" in r)
    return riga.strip().rsplit("/", 1)[-1]


@pytest.fixture
def staff(client, posta_inviata):
    """Greta, registrata e con l'email confermata: quindi staff."""
    registra(client, GRETA, nome="Greta", cognome="Lorenzetti")
    codice = codice_dal_link(posta_inviata[-1][2])
    r = client.post("/api/auth/conferma", json={"codice": codice})
    assert r.status_code == 200, r.text
    assert r.json()["utente"]["ruolo"] == "staff"
    return r.json()["token"]


@pytest.fixture
def cliente(client, posta_inviata):
    return registra(client, "sofia@example.com")["token"]


def lezioni(client, token, giorno="2026-10-12", giorni=1):
    r = client.get(f"/api/lezioni?da={giorno}&giorni={giorni}", headers=auth(token))
    assert r.status_code == 200, r.text
    return r.json()


def carica(client, staff_token, cliente_id, quante):
    r = client.post(f"/api/staff/clienti/{cliente_id}/lezioni", json={"lezioni": quante}, headers=auth(staff_token))
    assert r.status_code == 200, r.text
    return r.json()
