"""Configurazione dei test: database isolato in memoria per ogni test."""

import os
import tempfile

# Vanno impostate PRIMA di importare `app.core.config`, che legge le
# impostazioni a tempo di import.
# - con 12 round bcrypt la suite impiegherebbe minuti;
# - le foto dei test finiscono in una cartella temporanea, non fra quelle vere.
os.environ.setdefault("BCRYPT_ROUNDS", "4")
os.environ.setdefault("MEDIA_DIR", tempfile.mkdtemp(prefix="portale-test-media-"))

from io import BytesIO  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from PIL import Image  # noqa: E402

from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Zona  # noqa: E402


@pytest.fixture
def db_engine():
    """SQLite in memoria. StaticPool tiene viva la stessa connessione,
    altrimenti ogni sessione vedrebbe un database vuoto e diverso."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(db_engine):
    """Client HTTP con il database di test iniettato al posto di quello reale."""
    TestingSession = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    with TestingSession() as db:
        db.add_all(
            [
                Zona(nome="EUR", citta="Roma", macro_area="Municipio IX"),
                Zona(nome="Ostia / Acilia", citta="Roma", macro_area="Municipio X"),
            ]
        )
        db.commit()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # `lifespan` creerebbe lo schema sul database vero: qui non serve.
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Utilità condivise ----------------------------------------------------
def registra(client, email: str, tipo: str, password: str = "password123") -> dict:
    r = client.post(
        "/auth/registrazione",
        json={
            "email": email,
            "password": password,
            "tipo": tipo,
            "accetta_privacy": True,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def login(client, email: str, password: str = "password123") -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def bagnino(client):
    """Account bagnino con profilo e brevetto valido. Restituisce (token, ids)."""
    utente = registra(client, "bagnino@test.it", "bagnino")
    token = login(client, "bagnino@test.it")
    r = client.post(
        "/bagnini",
        json={"nome": "Marco", "cognome": "Rossi", "anni_esperienza": 5, "zone_ids": [1]},
        headers=auth(token),
    )
    assert r.status_code == 201, r.text
    client.post(
        "/bagnini/me/brevetti",
        json={"tipo": "MIP", "data_scadenza": "2030-01-01"},
        headers=auth(token),
    )
    return {"token": token, "utente_id": utente["id"], "profilo_id": r.json()["id"]}


def immagine_finta(dimensione=(60, 40), colore=(10, 110, 127), formato="PNG") -> bytes:
    """Un'immagine vera ma minuscola, per provare i caricamenti."""
    buffer = BytesIO()
    Image.new("RGB", dimensione, colore).save(buffer, formato)
    return buffer.getvalue()


def carica_foto(client, token, percorso, campo="file", **extra):
    return client.post(
        percorso,
        files={campo: ("prova.png", immagine_finta(), "image/png")},
        data=extra,
        headers=auth(token),
    )


@pytest.fixture
def piscina(client):
    """Account piscina con profilo e foto dell'ingresso.

    La foto serve: senza, la struttura non può pubblicare annunci.
    """
    utente = registra(client, "piscina@test.it", "piscina")
    token = login(client, "piscina@test.it")
    r = client.post(
        "/piscine",
        json={"nome_struttura": "Aqua Test", "tipo_struttura": "hotel", "zona_id": 1},
        headers=auth(token),
    )
    assert r.status_code == 201, r.text
    foto = carica_foto(client, token, "/piscine/me/foto", tipo="ingresso")
    assert foto.status_code == 201, foto.text
    return {"token": token, "utente_id": utente["id"], "profilo_id": r.json()["id"]}
