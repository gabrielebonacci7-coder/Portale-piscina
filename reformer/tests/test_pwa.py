"""L'app vera, guidata con un browser vero (Chromium, tramite Playwright).

Le prove in test_regole.py controllano il server; questa controlla che
l'interfaccia ci arrivi davvero: una cliente si registra e prenota, Greta le
carica le lezioni dal gestionale e la cliente le vede.

Il server gira su una porta a caso, con l'orologio vero (le altre prove lo
fermano a un lunedì, qui serve un server normale). Se Playwright o Chromium
non ci sono, la prova si salta.
"""

import socket
import threading
import time

import pytest

playwright = pytest.importorskip("playwright.sync_api")

CHROMIUM = "/opt/pw-browsers/chromium"


def _porta_libera() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server(monkeypatch):
    import uvicorn

    from reformer.dominio import orario
    from reformer.main import app

    # Qui l'orologio è quello vero: il conftest lo ferma, lo si rimette.
    from datetime import datetime, timezone
    monkeypatch.setattr(orario, "adesso", lambda: datetime.now(timezone.utc))
    monkeypatch.setattr(orario, "oggi", lambda: datetime.now(timezone.utc).astimezone(orario.FUSO).date())

    porta = _porta_libera()
    config = uvicorn.Config(app, host="127.0.0.1", port=porta, log_level="warning")
    srv = uvicorn.Server(config)
    t = threading.Thread(target=srv.run, daemon=True)
    t.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{porta}/"
    srv.should_exit = True
    t.join(timeout=5)


def test_dalla_registrazione_al_gestionale(server, posta_inviata):
    from pathlib import Path

    from reformer.tests.conftest import GRETA, codice_dal_link

    sp = playwright.sync_playwright().start()
    try:
        opzioni = {"executable_path": CHROMIUM} if Path(CHROMIUM).exists() else {}
        try:
            browser = sp.chromium.launch(**opzioni)
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"Chromium non disponibile: {e}")
        pg = browser.new_page(viewport={"width": 414, "height": 874})
        errori = []
        pg.on("pageerror", lambda e: errori.append(str(e)))

        # --- Greta si registra e conferma: diventa staff.
        pg.goto(server)
        pg.click("text=Crea il tuo account")
        for campo, valore in [("nome", "Greta"), ("cognome", "Lorenzetti"), ("telefono", "3791567202"),
                              ("email", GRETA), ("password", "greta2026!")]:
            pg.fill(f"#campo-{campo}", valore)
        pg.check("#campo-privacy")
        pg.click("button[type=submit]")
        pg.wait_for_selector(".benvenuto")
        pg.goto(server + "#/conferma/" + codice_dal_link(posta_inviata[-1][2]))
        pg.wait_for_selector("text=Gestionale")
        pg.click("a[href='#/profilo']")
        pg.click("text=Esci")

        # --- Una cliente si registra: senza pacchetto non può ancora prenotare.
        pg.click("text=Crea il tuo account")
        for campo, valore in [("nome", "Sofia"), ("cognome", "Marini"), ("telefono", "3331234567"),
                              ("email", "sofia@example.com"), ("password", "pilates2026")]:
            pg.fill(f"#campo-{campo}", valore)
        pg.check("#campo-privacy")
        pg.click("button[type=submit]")
        pg.click(".benvenuto .salta")
        pg.wait_for_selector(".striscia .giorno")

        def apri_lezione_libera():
            giorni = pg.locator(".striscia .giorno")
            for i in range(giorni.count()):
                giorni.nth(i).click()
                pg.wait_for_timeout(150)
                if pg.locator(".lezione.libera").count():
                    break
            pg.locator(".lezione.libera").first.click()

        apri_lezione_libera()
        pg.wait_for_selector("text=Hai finito le lezioni del pacchetto")
        assert pg.locator(".foglio .bottone.prenota").count() == 0
        pg.click(".foglio .tondo")
        pg.click("a[href='#/profilo']")
        pg.click("text=Esci")

        # --- Greta le carica 10 lezioni dal gestionale.
        pg.fill("#campo-email", GRETA)
        pg.fill("#campo-password", "greta2026!")
        pg.click("button[type=submit]")
        pg.wait_for_selector("text=Gestionale")
        pg.click(".tab a[href='#/studio/clienti']")
        pg.click("text=Sofia Marini")
        pg.wait_for_selector("#lezioni-rimaste")
        assert pg.input_value("#lezioni-rimaste") == "0"
        pg.click("text=+10")
        pg.click(".riquadro.carica .bottone.largo")
        pg.wait_for_function("document.querySelector('#lezioni-rimaste')?.value === '10'")
        pg.click("a[href='#/profilo']")
        pg.click("text=Esci")

        # --- La cliente prenota e vede le sue 9 lezioni.
        pg.fill("#campo-email", "sofia@example.com")
        pg.fill("#campo-password", "pilates2026")
        pg.click("button[type=submit]")
        pg.wait_for_selector(".striscia .giorno")
        apri_lezione_libera()
        pg.click(".foglio .bottone.prenota")
        pg.wait_for_selector("text=Prenotata!")
        pg.click(".conferma .bottone")
        pg.click(".tab a[href='#/pacchetto']")
        pg.wait_for_selector(".tessera-numero")
        assert pg.inner_text(".tessera-numero") == "9"

        assert errori == []
        browser.close()
    finally:
        sp.stop()
