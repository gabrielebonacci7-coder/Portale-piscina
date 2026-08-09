"""Registra il video dimostrativo di Guardlink.

    python -m scripts.video_demo            # video completo
    python -m scripts.video_demo --veloce   # pause dimezzate, per provare i tagli

Non è un mockup: guida l'applicazione vera dentro due telefoni affiancati e
registra quello che succede. Se l'app cambia, il video si rifà lanciando di
nuovo questo comando.

Perché due server sulla stessa applicazione: il token sta in localStorage, e
localStorage è legato all'origine. Due telefoni sulla stessa porta sarebbero
lo stesso utente; su due porte diverse sono due sessioni indipendenti.
"""

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
USCITA = RADICE / "demo"
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

PORTA_PISCINA = 8101
PORTA_BAGNINO = 8102
PORTA_PALCO = 8103

DB_DEMO = RADICE / "demo_video.db"
MEDIA_DEMO = RADICE / "media_video"

PISCINA = "info@aquacenter.example"
BAGNINO = "marco.rossi@example.com"
PASSWORD = "demo1234"

# Ritmo: medio, con il tempo di leggere le didascalie.
LENTO = 1.0


def pausa(secondi: float) -> None:
    time.sleep(secondi * LENTO)


def prossimo_sabato(ora: int) -> str:
    """Valore per <input type="datetime-local">: il prossimo sabato a `ora`.

    Un turno con un orario plausibile racconta meglio di uno "fra due ore".
    """
    from datetime import datetime, timedelta

    oggi = datetime.now()
    giorni = (5 - oggi.weekday()) % 7 or 7
    sabato = (oggi + timedelta(days=giorni)).replace(
        hour=ora, minute=0, second=0, microsecond=0
    )
    return sabato.strftime("%Y-%m-%dT%H:%M")


# ---------------------------------------------------------------- preparazione
def prepara_dati() -> None:
    """Database e foto dedicati al video, così il resto non viene toccato."""
    DB_DEMO.unlink(missing_ok=True)
    shutil.rmtree(MEDIA_DEMO, ignore_errors=True)

    ambiente = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{DB_DEMO}",
        "MEDIA_DIR": str(MEDIA_DEMO),
    }
    subprocess.run(
        [sys.executable, "-m", "scripts.seed_demo"],
        cwd=RADICE, env=ambiente, check=True, capture_output=True,
    )

    # WAL: due processi scrivono sullo stesso file, e senza questo il secondo
    # troverebbe il database bloccato.
    import sqlite3

    con = sqlite3.connect(DB_DEMO)
    con.execute("PRAGMA journal_mode=WAL")
    # Senza questo SQLite ignora le foreign key, e le cancellazioni qui sotto
    # lascerebbero candidature orfane che poi fanno andare l'API in errore.
    con.execute("PRAGMA foreign_keys=ON")
    # Si tolgono i due annunci che darebbero fastidio al racconto: il
    # "mattutino" perché è quello che pubblicheremo dal vivo, e l'altro
    # "urgente" perché, essendo prima nel tempo, resterebbe in cima al posto
    # del nostro e confonderebbe (due titoli quasi uguali).
    con.execute(
        "DELETE FROM annunci WHERE titolo LIKE 'Turno mattutino%'"
        " OR titolo LIKE 'Sostituzione urgente%'"
    )
    con.commit()
    con.close()


def porta_pronta(porta: int, secondi: int = 25) -> bool:
    scadenza = time.time() + secondi
    while time.time() < scadenza:
        with socket.socket() as s:
            s.settimeout(0.4)
            if s.connect_ex(("127.0.0.1", porta)) == 0:
                return True
        time.sleep(0.3)
    return False


def avvia_servizi() -> list[subprocess.Popen]:
    ambiente = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{DB_DEMO}",
        "MEDIA_DIR": str(MEDIA_DEMO),
    }
    processi = [
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", str(porta), "--log-level", "warning"],
            cwd=RADICE, env=ambiente,
            # I log finiscono su file: quando una scena fallisce, la causa
            # spesso è lato server e senza questi non si vedrebbe.
            stdout=open(USCITA / f"server-{porta}.log", "w"),
            stderr=subprocess.STDOUT,
        )
        for porta in (PORTA_PISCINA, PORTA_BAGNINO)
    ]
    processi.append(
        subprocess.Popen(
            [sys.executable, "-m", "http.server", str(PORTA_PALCO), "--bind", "127.0.0.1"],
            cwd=RADICE / "scripts" / "demo",
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    )
    for porta in (PORTA_PISCINA, PORTA_BAGNINO, PORTA_PALCO):
        if not porta_pronta(porta):
            raise RuntimeError(f"il servizio sulla porta {porta} non risponde")
    return processi


# ------------------------------------------------------------------ montaggio
def in_mp4(webm: Path, mp4: Path) -> None:
    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, "-y", "-i", str(webm),
         "-c:v", "libx264", "-preset", "slow", "-crf", "23",
         "-pix_fmt", "yuv420p",          # senza, molti lettori non lo aprono
         "-movflags", "+faststart",      # parte subito anche mentre si scarica
         "-r", "30", str(mp4)],
        check=True, capture_output=True,
    )


def copertina(webm: Path, jpg: Path, secondo: float = 12.0) -> None:
    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, "-y", "-ss", str(secondo), "-i", str(webm),
         "-frames:v", "1", "-q:v", "3", str(jpg)],
        check=True, capture_output=True,
    )


# -------------------------------------------------------------------- il video
def gira(pagina) -> None:
    """La sequenza. Ogni blocco è una scena del video."""
    piscina = pagina.frame_locator("#piscina")
    bagnino = pagina.frame_locator("#bagnino")

    def didascalia(passo, frase, attesa=2.6):
        pagina.evaluate(f"didascalia({passo!r}, {frase!r})")
        pausa(attesa)

    def attore(chi):
        pagina.evaluate(f"attore({chi!r})")

    def accedi(telefono, email):
        telefono.locator('input[name="email"]').fill(email)
        telefono.locator('input[name="password"]').fill(PASSWORD)
        telefono.locator('button[type="submit"]').click()
        telefono.locator(".tabs").wait_for(timeout=20000)

    # --- Scena 0: entrambi entrano ---
    attore("entrambi")
    didascalia("Guardlink", "Chi cerca un turno e chi lo offre, nello stesso posto.", 1.0)
    accedi(piscina, PISCINA)
    accedi(bagnino, BAGNINO)
    pausa(2.0)

    # --- Scena 1: la struttura pubblica ---
    attore("piscina")
    didascalia("1 · Pubblica", "Una piscina resta scoperta: pubblica il turno in trenta secondi.")
    piscina.locator('button[aria-label="Pubblica un annuncio"]').click()
    piscina.locator(".pannello").wait_for(timeout=10000)
    pausa(0.8)

    piscina.locator('.pannello input[type="text"]').first.type(
        "Sostituzione sabato pomeriggio", delay=45
    )
    pausa(0.4)
    # Inizio e fine: sabato 14-19, un turno vero.
    piscina.locator('.pannello input[type="datetime-local"]').first.fill(prossimo_sabato(14))
    piscina.locator('.pannello input[type="datetime-local"]').nth(1).fill(prossimo_sabato(19))
    pausa(0.4)
    piscina.locator(".pannello select").nth(0).select_option(label="EUR — Municipio IX")
    piscina.locator(".pannello select").nth(1).select_option("sostituzione_urgente")
    pausa(0.3)
    piscina.locator('.pannello input[type="number"]').first.type("14", delay=90)
    piscina.locator(".pannello select").nth(3).select_option("P")
    piscina.locator('.pannello input[type="checkbox"]').first.check()
    pausa(0.6)
    piscina.locator(".pannello textarea").fill(
        "Vasca da 25m, turno dalle 14 alle 19. Serve brevetto in corso di validità."
    )
    pausa(1.4)
    piscina.locator('.pannello button:has-text("Pubblica")').click()
    piscina.locator(".brindisi").wait_for(timeout=10000)
    pausa(2.0)

    # --- Scena 2: compare in bacheca ---
    attore("bagnino")
    # Didascalia breve e poi l'aggiornamento: così si vede il turno comparire
    # mentre la frase è ancora sullo schermo, invece che a cose già fatte.
    didascalia("2 · In bacheca", "Compare subito ai bagnini della zona. Gli urgenti vanno in cima.", 0.9)
    bagnino.locator('[data-scheda="profilo"]').click()
    pausa(0.4)
    bagnino.locator('[data-scheda="bacheca"]').click()  # ricarica la bacheca
    bagnino.locator('.scheda:has-text("Sostituzione sabato")').wait_for(timeout=15000)
    pausa(3.0)

    # --- Scena 3: il dettaglio, con la foto dell'ingresso ---
    didascalia("3 · Il turno", "Orario, compenso, e la foto dell'ingresso per trovare il posto.")
    bagnino.locator('.scheda:has-text("Sostituzione sabato")').click()
    bagnino.locator(".pannello").wait_for(timeout=10000)
    pausa(1.6)
    bagnino.locator(".pannello .galleria img").first.wait_for(timeout=10000)
    bagnino.locator(".pannello .galleria").scroll_into_view_if_needed()
    pausa(3.0)

    # --- Scena 4: la candidatura ---
    attore("bagnino")
    didascalia("4 · Ti candidi", "Un tocco, due righe di presentazione, ed è fatta.")
    bagnino.locator('.pannello button:has-text("Candidati")').click()
    bagnino.locator('.pannello button:has-text("Invia candidatura")').wait_for(timeout=10000)
    pausa(0.6)
    bagnino.locator(".pannello textarea").type(
        "Disponibile sabato, ho già lavorato da voi.", delay=38
    )
    pausa(1.0)
    bagnino.locator('.pannello button:has-text("Invia candidatura")').click()
    bagnino.locator(".brindisi").wait_for(timeout=10000)
    pausa(1.8)

    # --- Scena 5: la struttura vede chi ha risposto ---
    attore("piscina")
    didascalia("5 · Chi ha risposto", "La struttura vede le candidature. Solo lei: gli altri no.")
    piscina.locator('[data-scheda="candidature"]').click()
    piscina.locator(".elenco .scheda").first.wait_for(timeout=10000)
    pausa(1.4)
    piscina.locator('.scheda:has-text("Sostituzione sabato") button:has-text("in attesa")').click()
    piscina.locator(".pannello .blocco").first.wait_for(timeout=10000)
    pausa(2.4)

    # --- Scena 6: il profilo del candidato ---
    didascalia("6 · Chi è", "Brevetto valido, esperienza, recensioni di chi l'ha già chiamato.")
    piscina.locator('.pannello button:has-text("Vedi profilo")').first.click()
    piscina.locator(".pannello img.avatar.grande, .pannello .avatar.grande").first.wait_for(
        timeout=10000
    )
    pausa(2.2)
    piscina.locator('.pannello .blocco:has-text("BREVETTI")').scroll_into_view_if_needed()
    pausa(2.6)
    piscina.locator('.pannello button[aria-label="Chiudi"]').last.click()
    pausa(1.0)

    # --- Scena 7: accetta ---
    didascalia("7 · Accetta", "Il turno è assegnato. Le altre candidature si chiudono da sole.")
    piscina.locator('.pannello button:has-text("Accetta")').first.click()
    piscina.locator(".brindisi").wait_for(timeout=10000)
    pausa(2.4)
    piscina.locator('.pannello button[aria-label="Chiudi"]').last.click()
    pausa(0.6)

    # --- Scena 8: si mettono d'accordo ---
    attore("entrambi")
    didascalia("8 · Vi scrivete", "Chat interna: nessuno deve dare il proprio numero per parlare.")
    piscina.locator('[data-scheda="bacheca"]').click()
    pausa(0.4)
    piscina.locator('.segmenti button:has-text("Bagnini")').click()
    piscina.locator(".elenco .scheda").first.wait_for(timeout=10000)
    piscina.locator('.scheda:has-text("Marco Rossi")').click()
    piscina.locator('.pannello button:has-text("Scrivi un messaggio")').wait_for(timeout=10000)
    piscina.locator('.pannello button:has-text("Scrivi un messaggio")').click()
    piscina.locator(".pannello textarea").wait_for(timeout=10000)
    piscina.locator(".pannello textarea").type(
        "Ciao Marco, ti aspettiamo sabato alle 14 all'ingresso.", delay=32
    )
    pausa(0.8)
    piscina.locator('.pannello button:has-text("Invia")').click()
    piscina.locator(".brindisi").wait_for(timeout=10000)
    pausa(1.2)

    bagnino.locator('[data-scheda="messaggi"]').click()
    bagnino.locator(".elenco .scheda").first.wait_for(timeout=10000)
    pausa(1.6)
    bagnino.locator(".elenco .scheda").first.click()
    bagnino.locator(".chat .bolla").first.wait_for(timeout=10000)
    pausa(1.0)
    bagnino.locator(".composizione textarea").type("Perfetto, ci sono!", delay=45)
    pausa(0.5)
    bagnino.locator(".composizione button").click()
    pausa(2.2)
    bagnino.locator('.pannello button[aria-label="Chiudi"]').last.click()
    pausa(0.6)

    # --- Scena 9: turno concluso ---
    attore("piscina")
    didascalia("9 · Turno concluso", "A cose fatte la struttura chiude il turno.")
    piscina.locator('[data-scheda="candidature"]').click()
    piscina.locator(".elenco .scheda").first.wait_for(timeout=10000)
    pausa(0.8)
    piscina.locator('.scheda:has-text("Sostituzione sabato") button:has-text("Dettaglio")').click()
    piscina.locator('.pannello button:has-text("Segna come concluso")').wait_for(timeout=10000)
    pausa(1.0)
    piscina.locator('.pannello button:has-text("Segna come concluso")').click()
    piscina.locator(".brindisi").wait_for(timeout=10000)
    pausa(1.8)

    # --- Scena 10: le recensioni ---
    attore("bagnino")
    didascalia("10 · Vi recensite", "E si lascia una recensione. Da tutte e due le parti.")
    bagnino.locator('[data-scheda="bacheca"]').click()
    pausa(0.3)
    bagnino.locator('[data-scheda="candidature"]').click()
    bagnino.locator('button:has-text("Recensisci la struttura")').first.wait_for(timeout=10000)
    pausa(1.0)
    bagnino.locator('button:has-text("Recensisci la struttura")').first.click()
    bagnino.locator(".pannello .voti-stelle").first.wait_for(timeout=10000)
    pausa(0.8)

    # Le stelle si accendono una alla volta: si vede che è una scelta.
    for i in range(5):
        bagnino.locator(".pannello .campo .voti-stelle button").nth(i).click()
        pausa(0.18)
    pausa(0.5)
    for riga in range(2):
        for i in range(5):
            bagnino.locator(".pannello .voce").nth(riga).locator("button").nth(i).click()
            pausa(0.09)
    pausa(0.6)
    bagnino.locator(".pannello textarea").type(
        "Ambiente serio e pagamento puntuale. Ci torno volentieri.", delay=30
    )
    pausa(1.2)
    bagnino.locator('.pannello button:has-text("Invia recensione")').click()
    bagnino.locator(".brindisi").wait_for(timeout=10000)
    pausa(2.4)

    # --- Chiusura ---
    attore("entrambi")
    didascalia("", "Dalla ricerca al turno svolto, senza uscire dall'app.", 2.8)
    pagina.evaluate("sipario()")
    pausa(3.4)


def main() -> int:
    global LENTO

    parser = argparse.ArgumentParser(description="Registra il video dimostrativo.")
    parser.add_argument("--veloce", action="store_true", help="dimezza le pause")
    argomenti = parser.parse_args()
    if argomenti.veloce:
        LENTO = 0.5

    from playwright.sync_api import sync_playwright

    USCITA.mkdir(exist_ok=True)
    grezzi = USCITA / "grezzo"
    shutil.rmtree(grezzi, ignore_errors=True)

    USCITA.mkdir(exist_ok=True)

    print("Preparo i dati…")
    prepara_dati()

    print("Avvio i servizi…")
    processi = avvia_servizi()

    errori = []
    try:
        print("Registro…")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=CHROMIUM,
                args=["--autoplay-policy=no-user-gesture-required"],
            )
            contesto = browser.new_context(
                viewport={"width": 1080, "height": 1350},
                locale="it-IT",
                record_video_dir=str(grezzi),
                record_video_size={"width": 1080, "height": 1350},
            )
            pagina = contesto.new_page()
            # `pageerror` copre solo la pagina esterna: le eccezioni dentro i
            # telefoni arrivano dalla console, che invece vede tutti i riquadri.
            pagina.on("pageerror", lambda e: errori.append(f"palco: {e}"))
            pagina.on(
                "console",
                lambda m: errori.append(f"{m.type}: {m.text}")
                if m.type == "error" and "Failed to load resource" not in m.text
                else None,
            )

            pagina.goto(f"http://127.0.0.1:{PORTA_PALCO}/palco.html", wait_until="load")
            pagina.evaluate(
                f"avvia('http://127.0.0.1:{PORTA_PISCINA}/', 'http://127.0.0.1:{PORTA_BAGNINO}/')"
            )
            pagina.frame_locator("#piscina").locator(".accesso").wait_for(timeout=25000)
            pagina.frame_locator("#bagnino").locator(".accesso").wait_for(timeout=25000)
            pausa(1.2)

            try:
                gira(pagina)
            except Exception:
                # Se una scena non trova quello che si aspetta, si salva
                # com'era lo schermo: capire cosa c'era è molto più veloce
                # che rileggere lo script.
                pagina.screenshot(path=str(USCITA / "errore.png"))
                print(f"Scena fallita: schermata salvata in {USCITA / 'errore.png'}")
                for e in errori:
                    print("  !", e)
                raise

            contesto.close()
            browser.close()
    finally:
        for p in processi:
            p.send_signal(signal.SIGTERM)
        for p in processi:
            p.wait(timeout=10)

    webm = next(grezzi.glob("*.webm"))
    mp4 = USCITA / "guardlink-demo.mp4"
    jpg = USCITA / "guardlink-copertina.jpg"

    print("Converto in MP4…")
    in_mp4(webm, mp4)
    copertina(webm, jpg)
    shutil.rmtree(grezzi, ignore_errors=True)

    DB_DEMO.unlink(missing_ok=True)
    Path(str(DB_DEMO) + "-wal").unlink(missing_ok=True)
    Path(str(DB_DEMO) + "-shm").unlink(missing_ok=True)
    shutil.rmtree(MEDIA_DEMO, ignore_errors=True)

    print(f"\nVideo:     {mp4}  ({mp4.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"Copertina: {jpg}  ({jpg.stat().st_size / 1024:.0f} kB)")
    if errori:
        print(f"\nErrori JavaScript durante la registrazione: {len(errori)}")
        for e in errori:
            print("  !", e)
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
