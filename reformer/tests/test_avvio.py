"""Online l'app non parte con una configurazione da sviluppo."""

import pytest

from reformer.core.config import settings
from reformer.main import controlla_configurazione


@pytest.mark.parametrize("chiave,url,errore", [
    (settings.secret_key, "https://reformer.it", "di sviluppo"),
    ("", "https://reformer.it", "vuota o troppo corta"),
    ("x" * 64, "http://127.0.0.1:8002", "indirizzo locale"),
])
def test_configurazione_non_pronta(monkeypatch, chiave, url, errore):
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "secret_key", chiave)
    monkeypatch.setattr(settings, "url_pubblico", url)
    with pytest.raises(RuntimeError, match=errore):
        controlla_configurazione()


def test_configurazione_pronta(monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "secret_key", "a" * 64)
    monkeypatch.setattr(settings, "url_pubblico", "https://reformer.it")
    controlla_configurazione()
