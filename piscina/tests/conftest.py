"""Impianto dei test: un database vuoto per ogni prova."""

import os
import tempfile

# Vanno impostate prima di importare qualsiasi cosa del progetto: la
# configurazione si legge una volta sola, all'import.
_TEMP = tempfile.mkdtemp(prefix="piscina-test-")
os.environ["PISCINA_DATABASE_URL"] = f"sqlite:///{_TEMP}/prova.db"
os.environ["PISCINA_BCRYPT_ROUNDS"] = "4"  # altrimenti i test durano minuti
os.environ["PISCINA_EMAIL_SMTP_HOST"] = ""  # niente email vere
os.environ["PISCINA_EMAIL_STAFF"] = "cassa@example.com"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from piscina.core import limiti  # noqa: E402
from piscina.core.security import hash_password  # noqa: E402
from piscina.db.init_db import sincronizza_postazioni  # noqa: E402
from piscina.db.session import SessionLocal, engine  # noqa: E402
from piscina.main import app  # noqa: E402
from piscina.models import Base, Operatore  # noqa: E402

PASSWORD_STAFF = "cassa-di-prova"


@pytest.fixture()
def db():
    """Database pulito, con le postazioni della piantina già dentro."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    limiti.azzera_tutto()
    with SessionLocal() as sessione:
        sincronizza_postazioni(sessione)
        yield sessione


@pytest.fixture()
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def operatore(db) -> Operatore:
    o = Operatore(
        email="cassa@example.com",
        nome="Cassa",
        password_hash=hash_password(PASSWORD_STAFF),
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@pytest.fixture()
def staff(client, operatore):
    """Un client con il token dello staff già in tasca."""
    risposta = client.post(
        "/api/staff/accesso",
        json={"email": operatore.email, "password": PASSWORD_STAFF},
    )
    assert risposta.status_code == 200, risposta.text
    client.headers["Authorization"] = f"Bearer {risposta.json()['token']}"
    return client
