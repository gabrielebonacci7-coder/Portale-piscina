"""Le due difese che valgono solo online: controlli all'avvio e limiti ai tentativi."""

import pytest

from app.core import limiti
from app.core.avvio import (
    CHIAVE_DI_SVILUPPO,
    ConfigurazioneNonValida,
    controlla_o_esplodi,
    in_produzione,
    verifica_configurazione,
)
from app.core.config import settings
from tests.conftest import auth, registra


@pytest.fixture(autouse=True)
def contatori_puliti():
    """Ogni test riparte da zero: i limiti stanno in memoria e sono condivisi."""
    limiti.svuota_tutto()
    yield
    limiti.svuota_tutto()


@pytest.fixture
def online(monkeypatch):
    """Configurazione da server pubblico, fatta bene."""
    monkeypatch.setattr(settings, "url_pubblico", "https://guardlink.it")
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "secret_key", "a" * 64)
    monkeypatch.setattr(settings, "email_smtp_host", "smtp.esempio.it")


# --- Controlli all'avvio ----------------------------------------------------
def test_in_locale_non_scatta_niente():
    """Sviluppare deve restare comodo: i controlli si attivano solo online."""
    assert in_produzione() is False
    assert verifica_configurazione() == []


def test_una_configurazione_giusta_passa(online):
    assert in_produzione() is True
    assert verifica_configurazione() == []
    controlla_o_esplodi()  # non solleva


def test_la_chiave_di_sviluppo_blocca_l_avvio(online, monkeypatch):
    """È il controllo che conta di più: quella chiave sta scritta su GitHub."""
    monkeypatch.setattr(settings, "secret_key", CHIAVE_DI_SVILUPPO)
    with pytest.raises(ConfigurazioneNonValida) as errore:
        controlla_o_esplodi()
    assert "SECRET_KEY" in str(errore.value)


def test_debug_acceso_online_blocca(online, monkeypatch):
    monkeypatch.setattr(settings, "debug", True)
    problemi = " ".join(verifica_configurazione())
    assert "DEBUG" in problemi


def test_indirizzo_pubblico_senza_https_blocca(online, monkeypatch):
    monkeypatch.setattr(settings, "url_pubblico", "http://guardlink.it")
    assert any("https" in p for p in verifica_configurazione())


def test_posta_non_configurata_blocca(online, monkeypatch):
    monkeypatch.setattr(settings, "email_smtp_host", "")
    assert any("EMAIL_SMTP_HOST" in p for p in verifica_configurazione())


def test_basta_un_indirizzo_pubblico_anche_con_debug_dimenticato(monkeypatch):
    """Chi mette l'indirizzo vero e si scorda DEBUG=false è comunque online."""
    monkeypatch.setattr(settings, "url_pubblico", "https://guardlink.it")
    monkeypatch.setattr(settings, "debug", True)
    assert in_produzione() is True


# --- Limiti ai tentativi ----------------------------------------------------
def test_dopo_troppi_login_sbagliati_si_viene_fermati(client):
    registra(client, "vittima@test.it", "bagnino")

    # Il limite per indirizzo è il più stretto dei due.
    for _ in range(settings.limite_login_per_email):
        r = client.post(
            "/auth/login", json={"email": "vittima@test.it", "password": "sbagliata"}
        )
        assert r.status_code == 401

    r = client.post("/auth/login", json={"email": "vittima@test.it", "password": "sbagliata"})
    assert r.status_code == 429
    assert "Retry-After" in r.headers

    # E non si passa nemmeno con la password giusta: il blocco è sul tentativo.
    r = client.post("/auth/login", json={"email": "vittima@test.it", "password": "password123"})
    assert r.status_code == 429


def test_entrare_azzera_il_contatore(client):
    registra(client, "distratto@test.it", "bagnino")

    # Qualche errore di battitura, ma sotto la soglia.
    for _ in range(settings.limite_login_per_email - 1):
        client.post("/auth/login", json={"email": "distratto@test.it", "password": "quasi"})

    r = client.post("/auth/login", json={"email": "distratto@test.it", "password": "password123"})
    assert r.status_code == 200

    # Da qui si ricomincia a contare da zero.
    for _ in range(settings.limite_login_per_email - 1):
        r = client.post("/auth/login", json={"email": "distratto@test.it", "password": "quasi"})
        assert r.status_code == 401


def test_il_limite_e_per_indirizzo_non_globale(client):
    """Chi sbaglia la sua password non deve chiudere fuori gli altri."""
    registra(client, "primo@test.it", "bagnino")
    registra(client, "secondo@test.it", "bagnino")

    for _ in range(settings.limite_login_per_email + 2):
        client.post("/auth/login", json={"email": "primo@test.it", "password": "no"})

    # Il secondo account non è stato toccato: il limite per IP è largo apposta,
    # perché in piscina stanno tutti sullo stesso wi-fi.
    r = client.post("/auth/login", json={"email": "secondo@test.it", "password": "password123"})
    assert r.status_code == 200


def test_anche_il_recupero_password_ha_un_limite(client):
    """Non protegge un account: evita di riempire di email una casella altrui."""
    for _ in range(settings.limite_recuperi):
        r = client.post("/auth/recupero-password", json={"email": "chiunque@test.it"})
        assert r.status_code == 204

    r = client.post("/auth/recupero-password", json={"email": "chiunque@test.it"})
    assert r.status_code == 429


def test_l_ip_inoltrato_si_ignora_se_non_c_e_un_proxy(client, monkeypatch):
    """Senza proxy davanti, `X-Forwarded-For` se lo scrive il client.

    Fidarsene vorrebbe dire lasciare che chiunque cambi identità a ogni
    tentativo, cioè non avere nessun limite.
    """
    monkeypatch.setattr(settings, "dietro_proxy", False)
    for numero in range(settings.limite_recuperi):
        r = client.post(
            "/auth/recupero-password",
            json={"email": "tizio@test.it"},
            headers={"X-Forwarded-For": f"10.0.0.{numero}"},
        )
        assert r.status_code == 204

    r = client.post(
        "/auth/recupero-password",
        json={"email": "tizio@test.it"},
        headers={"X-Forwarded-For": "10.0.0.99"},
    )
    assert r.status_code == 429


def test_con_un_proxy_davanti_l_ip_inoltrato_conta(client, monkeypatch):
    """Dietro Caddy, senza leggere quell'intestazione tutti avrebbero lo stesso IP."""
    monkeypatch.setattr(settings, "dietro_proxy", True)
    for numero in range(settings.limite_recuperi + 3):
        r = client.post(
            "/auth/recupero-password",
            json={"email": "tizio@test.it"},
            headers={"X-Forwarded-For": f"10.0.0.{numero}, 172.18.0.2"},
        )
        assert r.status_code == 204


def test_le_rotte_normali_non_sono_limitate(client, bagnino):
    """Il limite sta sulle porte d'ingresso, non sull'uso quotidiano."""
    for _ in range(30):
        r = client.get("/annunci", headers=auth(bagnino["token"]))
        assert r.status_code == 200
