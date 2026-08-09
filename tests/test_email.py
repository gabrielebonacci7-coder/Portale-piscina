"""Invio della posta: le due strade (log e SMTP) e cosa succede se fallisce.

Non si spedisce niente per davvero: si sostituisce `smtplib` con un finto
server e si guarda cosa gli viene chiesto. Serve perché l'errore vero, in
esercizio, non lo vede nessuno — l'app risponde "fatto" comunque.
"""

import smtplib

import pytest

from app.core import email as posta
from app.core.config import settings


class FintoSMTP:
    """Registra quello che il codice gli chiede, senza aprire nessuna connessione."""

    ultima = None

    def __init__(self, host, porta, timeout=None):
        FintoSMTP.ultima = self
        self.host = host
        self.porta = porta
        self.cifrato_dopo = False
        self.credenziali = None
        self.messaggio = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def starttls(self):
        self.cifrato_dopo = True

    def login(self, utente, password):
        self.credenziali = (utente, password)

    def send_message(self, messaggio):
        self.messaggio = messaggio


@pytest.fixture
def smtp_configurato(monkeypatch):
    monkeypatch.setattr(settings, "email_smtp_host", "smtp.esempio.it")
    monkeypatch.setattr(settings, "email_smtp_porta", 587)
    monkeypatch.setattr(settings, "email_smtp_utente", "io@esempio.it")
    monkeypatch.setattr(settings, "email_smtp_password", "segreta")
    monkeypatch.setattr(settings, "email_mittente", "Guardlink <io@esempio.it>")
    monkeypatch.setattr(smtplib, "SMTP", FintoSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FintoSMTP)
    FintoSMTP.ultima = None


def test_senza_host_finisce_nel_log(monkeypatch, caplog):
    """Senza SMTP il messaggio si legge nel log, link compreso."""
    monkeypatch.setattr(settings, "email_smtp_host", "")
    with caplog.at_level("WARNING", logger="guardlink.email"):
        posta.email_recupero("marco@esempio.it", "https://guardlink.it/?recupero=ABC")

    testo = caplog.text
    assert "EMAIL non spedita" in testo
    assert "marco@esempio.it" in testo
    # Il link deve esserci per intero: è tutto il motivo per cui si logga.
    assert "https://guardlink.it/?recupero=ABC" in testo


def test_con_host_spedisce_davvero(smtp_configurato):
    posta.email_recupero("marco@esempio.it", "https://guardlink.it/?recupero=ABC")

    finto = FintoSMTP.ultima
    assert (finto.host, finto.porta) == ("smtp.esempio.it", 587)
    assert finto.cifrato_dopo, "sulla 587 la connessione va cifrata con STARTTLS"
    assert finto.credenziali == ("io@esempio.it", "segreta")

    messaggio = finto.messaggio
    assert messaggio["To"] == "marco@esempio.it"
    assert messaggio["From"] == "Guardlink <io@esempio.it>"
    assert "password" in messaggio["Subject"].lower()
    assert "https://guardlink.it/?recupero=ABC" in messaggio.get_content()


def test_porta_465_e_gia_cifrata(smtp_configurato, monkeypatch):
    """Sulla 465 si parte cifrati: chiedere STARTTLS dopo darebbe errore."""
    monkeypatch.setattr(settings, "email_smtp_porta", 465)
    posta.invia_email("marco@esempio.it", "Prova", "corpo")
    assert FintoSMTP.ultima.cifrato_dopo is False


def test_senza_utente_non_fa_il_login(smtp_configurato, monkeypatch):
    """Alcuni relay interni non vogliono credenziali."""
    monkeypatch.setattr(settings, "email_smtp_utente", "")
    posta.invia_email("marco@esempio.it", "Prova", "corpo")
    assert FintoSMTP.ultima.credenziali is None


def test_un_guasto_diventa_ErroreInvio(smtp_configurato, monkeypatch):
    """Qualsiasi guasto SMTP esce come ErroreInvio, con la causa allegata.

    La causa serve: è quella che `scripts/prova_email` traduce in italiano.
    """
    def esplode(*_a, **_k):
        raise smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")

    monkeypatch.setattr(smtplib, "SMTP", esplode)

    with pytest.raises(posta.ErroreInvio) as errore:
        posta.invia_email("marco@esempio.it", "Prova", "corpo")
    assert isinstance(errore.value.__cause__, smtplib.SMTPAuthenticationError)


def test_il_recupero_non_rivela_il_guasto(client, smtp_configurato, monkeypatch):
    """Se la posta è rotta, l'utente riceve comunque 204.

    Sembra strano ed è voluto: un errore visibile direbbe a chiunque quali
    indirizzi sono registrati. Il guasto si vede solo nel log del server.
    """
    from tests.conftest import registra

    registra(client, "marco@esempio.it", "bagnino")

    def esplode(*_a, **_k):
        raise OSError("server di posta irraggiungibile")

    monkeypatch.setattr(smtplib, "SMTP", esplode)

    r = client.post("/auth/recupero-password", json={"email": "marco@esempio.it"})
    assert r.status_code == 204
