"""Recupero password e verifica dell'indirizzo email."""

import re

import pytest

from app.core.config import settings
from app.crud import token_email as crud_token
from app.models import TipoToken
from tests.conftest import auth, login, registra


def codice_dal_log(caplog, tipo: str = "recupero") -> str:
    """Estrae il codice dal link scritto nel log.

    Senza SMTP configurato le email finiscono lì: è lo stesso percorso che
    userebbe una persona, solo che il link si legge dal terminale.
    """
    testo = caplog.text
    trovati = re.findall(rf"\?{tipo}=([A-Za-z0-9_-]+)", testo)
    assert trovati, f"nessun link '{tipo}' nel log:\n{testo}"
    return trovati[-1]


# --- Recupero password ----------------------------------------------------
def test_giro_completo_di_recupero(client, caplog):
    registra(client, "dimenticata@test.it", "bagnino")

    with caplog.at_level("WARNING", logger="guardlink.email"):
        r = client.post("/auth/recupero-password", json={"email": "dimenticata@test.it"})
    assert r.status_code == 204

    codice = codice_dal_log(caplog, "recupero")
    r = client.post(
        "/auth/reimposta-password",
        json={"codice": codice, "password_nuova": "nuovissima1"},
    )
    assert r.status_code == 200, r.text
    # Si entra subito, senza dover rifare il login a mano.
    assert r.json()["access_token"]

    assert login(client, "dimenticata@test.it", "nuovissima1")
    # E la vecchia non vale più.
    vecchia = client.post(
        "/auth/login", json={"email": "dimenticata@test.it", "password": "password123"}
    )
    assert vecchia.status_code == 401


def test_email_sconosciuta_risponde_uguale(client, caplog):
    """Non si deve poter capire quali indirizzi sono registrati."""
    registra(client, "esiste@test.it", "bagnino")

    with caplog.at_level("WARNING", logger="guardlink.email"):
        esistente = client.post("/auth/recupero-password", json={"email": "esiste@test.it"})
        inesistente = client.post("/auth/recupero-password", json={"email": "mai@test.it"})

    assert esistente.status_code == inesistente.status_code == 204
    assert esistente.text == inesistente.text == ""


def test_il_codice_si_usa_una_volta_sola(client, caplog):
    registra(client, "unavolta@test.it", "bagnino")
    with caplog.at_level("WARNING", logger="guardlink.email"):
        client.post("/auth/recupero-password", json={"email": "unavolta@test.it"})
    codice = codice_dal_log(caplog, "recupero")

    corpo = {"codice": codice, "password_nuova": "primapassword"}
    assert client.post("/auth/reimposta-password", json=corpo).status_code == 200
    r = client.post(
        "/auth/reimposta-password", json={"codice": codice, "password_nuova": "secondapass"}
    )
    assert r.status_code == 400
    # La password è rimasta la prima.
    assert login(client, "unavolta@test.it", "primapassword")


def test_chiedere_un_nuovo_link_annulla_il_precedente(client, caplog):
    registra(client, "duelink@test.it", "bagnino")
    with caplog.at_level("WARNING", logger="guardlink.email"):
        client.post("/auth/recupero-password", json={"email": "duelink@test.it"})
        primo = codice_dal_log(caplog, "recupero")
        caplog.clear()
        client.post("/auth/recupero-password", json={"email": "duelink@test.it"})
        secondo = codice_dal_log(caplog, "recupero")

    assert primo != secondo
    # Il vecchio non deve restare una chiave buona in giro.
    r = client.post(
        "/auth/reimposta-password", json={"codice": primo, "password_nuova": "qualcosa1"}
    )
    assert r.status_code == 400
    assert client.post(
        "/auth/reimposta-password", json={"codice": secondo, "password_nuova": "qualcosa1"}
    ).status_code == 200


def test_codice_inventato_rifiutato(client):
    r = client.post(
        "/auth/reimposta-password",
        json={"codice": "questo-non-esiste-proprio", "password_nuova": "password123"},
    )
    assert r.status_code == 400


def test_password_nuova_troppo_corta(client, caplog):
    registra(client, "corta2@test.it", "bagnino")
    with caplog.at_level("WARNING", logger="guardlink.email"):
        client.post("/auth/recupero-password", json={"email": "corta2@test.it"})
    codice = codice_dal_log(caplog, "recupero")
    r = client.post("/auth/reimposta-password", json={"codice": codice, "password_nuova": "abc"})
    assert r.status_code == 422


def test_token_scaduto_non_vale(client, db_engine, caplog):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy.orm import sessionmaker

    from app.models import TokenEmail

    registra(client, "scaduto2@test.it", "bagnino")
    with caplog.at_level("WARNING", logger="guardlink.email"):
        client.post("/auth/recupero-password", json={"email": "scaduto2@test.it"})
    codice = codice_dal_log(caplog, "recupero")

    # Si sposta indietro la scadenza, invece di aspettare mezz'ora.
    with sessionmaker(bind=db_engine)() as db:
        token = (
            db.query(TokenEmail)
            .filter(TokenEmail.impronta == crud_token.impronta(codice))
            .one()
        )
        token.scade_il = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    r = client.post(
        "/auth/reimposta-password", json={"codice": codice, "password_nuova": "password123"}
    )
    assert r.status_code == 400


def test_nel_database_non_finisce_il_codice(client, db_engine, caplog):
    """Chi legge una copia del database non deve poter entrare negli account."""
    from sqlalchemy.orm import sessionmaker

    from app.models import TokenEmail

    registra(client, "impronta@test.it", "bagnino")
    with caplog.at_level("WARNING", logger="guardlink.email"):
        client.post("/auth/recupero-password", json={"email": "impronta@test.it"})
    codice = codice_dal_log(caplog, "recupero")

    with sessionmaker(bind=db_engine)() as db:
        salvate = [t.impronta for t in db.query(TokenEmail).all()]

    assert codice not in salvate
    assert crud_token.impronta(codice) in salvate


# --- Verifica dell'indirizzo ----------------------------------------------
def test_alla_registrazione_parte_la_verifica(client, caplog):
    with caplog.at_level("WARNING", logger="guardlink.email"):
        utente = registra(client, "daverificare@test.it", "bagnino")

    assert utente["email_verificata"] is False
    codice = codice_dal_log(caplog, "verifica")

    r = client.post("/auth/verifica-email", json={"codice": codice})
    assert r.status_code == 200
    assert r.json()["email_verificata"] is True


def test_rimanda_il_link_di_verifica(client, caplog):
    registra(client, "rimanda@test.it", "bagnino")
    token = login(client, "rimanda@test.it")

    with caplog.at_level("WARNING", logger="guardlink.email"):
        r = client.post("/auth/invia-verifica", headers=auth(token))
    assert r.status_code == 204
    codice = codice_dal_log(caplog, "verifica")

    assert client.post("/auth/verifica-email", json={"codice": codice}).status_code == 200
    # Già confermato: non ha senso rimandarlo.
    assert client.post("/auth/invia-verifica", headers=auth(token)).status_code == 409


def test_reimpostare_la_password_conferma_anche_l_indirizzo(client, caplog):
    """Chi apre il link ha dimostrato di leggere quella casella."""
    registra(client, "duepiccioni@test.it", "bagnino")
    with caplog.at_level("WARNING", logger="guardlink.email"):
        client.post("/auth/recupero-password", json={"email": "duepiccioni@test.it"})
    codice = codice_dal_log(caplog, "recupero")

    r = client.post(
        "/auth/reimposta-password", json={"codice": codice, "password_nuova": "password123"}
    )
    assert r.json()["utente"]["email_verificata"] is True


def test_un_codice_di_verifica_non_reimposta_la_password(client, caplog):
    """I due tipi di codice non sono intercambiabili."""
    registra(client, "tipisbagliati@test.it", "bagnino")
    with caplog.at_level("WARNING", logger="guardlink.email"):
        codice_verifica = codice_dal_log(caplog, "verifica")

    r = client.post(
        "/auth/reimposta-password",
        json={"codice": codice_verifica, "password_nuova": "password123"},
    )
    assert r.status_code == 400


@pytest.mark.parametrize(
    "percorso", ["/auth/recupero-password", "/auth/reimposta-password", "/auth/verifica-email"]
)
def test_sono_raggiungibili_senza_login(client, percorso):
    """Chi ha perso la password non può autenticarsi: devono essere pubblici."""
    r = client.post(percorso, json={})
    assert r.status_code == 422  # dati mancanti, non 401


def test_senza_smtp_le_email_finiscono_nel_log(client, caplog):
    """Il ripiego di sviluppo dev'essere visibile, non silenzioso."""
    assert settings.email_smtp_host == ""
    with caplog.at_level("WARNING", logger="guardlink.email"):
        registra(client, "nellog@test.it", "bagnino")
    assert "EMAIL non spedita" in caplog.text


def test_durata_dei_due_tipi(client, db_engine, caplog):
    """Il recupero vale poco, la verifica può aspettare."""
    from sqlalchemy.orm import sessionmaker

    from app.models import TokenEmail

    with caplog.at_level("WARNING", logger="guardlink.email"):
        registra(client, "durate@test.it", "bagnino")
        client.post("/auth/recupero-password", json={"email": "durate@test.it"})

    with sessionmaker(bind=db_engine)() as db:
        durate = {t.tipo: (t.scade_il - t.creato_il).total_seconds() for t in db.query(TokenEmail)}

    assert durate[TipoToken.RECUPERO_PASSWORD] < durate[TipoToken.VERIFICA_EMAIL]
    assert durate[TipoToken.RECUPERO_PASSWORD] == pytest.approx(
        settings.minuti_validita_recupero * 60, abs=5
    )
