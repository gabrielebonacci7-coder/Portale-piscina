"""Shoots the RE FORMER presentation video from the real app.

    python reformer/video/gira.py            # full video (~2.5 minutes)
    python reformer/video/gira.py --veloce   # halved pauses, to check the cuts

It doesn't edit still images together: it starts the real server (with a
throwaway database full of demo clients), drives the app inside a phone on a
stage and films the screen. If the app changes, the video is rebuilt by
running this command again.

Output is vertical 1080×1920 (LinkedIn, Instagram, WhatsApp), silent, with
English captions. Files land in reformer/video/uscita/: video.mp4,
copertina.jpg and copione.txt (when each caption appears).

Needs Playwright (pip install playwright) and ffmpeg.
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

RADICE = Path(__file__).resolve().parents[2]
USCITA = Path(__file__).resolve().parent / "uscita"
CHROMIUM = "/opt/pw-browsers/chromium"
PORTA_APP, PORTA_PALCO = 8002, 8003
LARGO, ALTO = 1080, 1920
LENTO = 1.0
ROMA = ZoneInfo("Europe/Rome")

COPIONE: list[tuple[float, str, str]] = []
AVVIO = 0.0
COPERTINA = [0.0]


def pausa(s: float) -> None:
    time.sleep(s * LENTO)


# ---------------------------------------------------------------- preparation
def ambiente() -> dict:
    return {
        **os.environ,
        "REFORMER_DATABASE_URL": f"sqlite:///{USCITA / 'video.db'}",
        "REFORMER_BCRYPT_ROUNDS": "4",
        "REFORMER_PROMEMORIA_ATTIVI": "false",
        "REFORMER_EMAIL_SMTP_HOST": "",
        # Nel video la cliente appena iscritta prenota prima che lo studio le
        # carichi il pacchetto: solo qui si concedono 2 lezioni a credito.
        "REFORMER_MAX_LEZIONI_DA_SALDARE": "2",
    }


def porta_pronta(porta: int, secondi: int = 25) -> bool:
    fine = time.time() + secondi
    while time.time() < fine:
        with socket.socket() as s:
            s.settimeout(0.4)
            if s.connect_ex(("127.0.0.1", porta)) == 0:
                return True
        time.sleep(0.25)
    return False


def chiama(metodo: str, percorso: str, corpo=None, token: str | None = None):
    richiesta = urllib.request.Request(
        f"http://127.0.0.1:{PORTA_APP}{percorso}", method=metodo,
        data=None if corpo is None else json.dumps(corpo).encode(),
        headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})},
    )
    try:
        with urllib.request.urlopen(richiesta, timeout=20) as r:
            testo = r.read()
            return json.loads(testo) if testo else None
    except urllib.error.HTTPError:
        return None


# ------------------------------------------------------------------- assembly
def in_mp4(webm: Path, mp4: Path) -> None:
    subprocess.run(
        [shutil.which("ffmpeg") or "ffmpeg", "-y", "-i", str(webm), "-c:v", "libx264", "-preset", "slow", "-crf", "20",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-r", "30", str(mp4)],
        check=True, capture_output=True,
    )


def copertina(mp4: Path, jpg: Path, secondo: float) -> None:
    subprocess.run([shutil.which("ffmpeg") or "ffmpeg", "-y", "-ss", str(secondo), "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(jpg)],
                   check=True, capture_output=True)


def scrivi_copione(percorso: Path) -> None:
    righe = ["Script — when each caption appears", ""]
    for t, passo, frase in COPIONE:
        m, s = divmod(t, 60)
        righe.append(f"{int(m):02d}:{s:05.2f}  [{passo}] {frase}")
    percorso.write_text("\n".join(righe) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ the video
def gira(pagina, giorno_prenota: str, giorno_pieno: str) -> None:
    app = pagina.frame_locator("#app")

    def didascalia(passo, frase, attesa=2.6):
        COPIONE.append((time.monotonic() - AVVIO, passo, frase))
        pagina.evaluate("([p, f]) => didascalia(p, f)", [passo, frase])
        pausa(attesa)

    def tocca(elemento, attesa=1.1):
        """Shows the finger, then really taps."""
        elemento.wait_for(timeout=20000)
        elemento.scroll_into_view_if_needed()
        r = elemento.bounding_box()
        if r:
            pagina.evaluate("([x, y]) => tocco(x, y)", [r["x"] + r["width"] / 2, r["y"] + r["height"] / 2])
            pausa(0.35)
        elemento.click()
        pausa(attesa)

    def scrivi(campo, testo, attesa=0.2):
        campo.click()
        campo.type(testo, delay=26 * LENTO)
        pausa(attesa)

    def esci():
        tocca(app.locator('a[href="#/profilo"]'), 0.8)
        tocca(app.locator('button:has-text("Esci")').last, 1.0)
        app.locator(".accesso").wait_for(timeout=15000)

    # 1. Intro
    app.locator(".accesso").wait_for(timeout=20000)
    didascalia("RE FORMER", "A booking app for a pilates reformer studio.", 2.8)

    # 2. Sign up
    tocca(app.locator('a[href="#/registrati"]'), 0.6)
    didascalia("Sign up", "Clients register once, in under a minute.", 0.5)
    scrivi(app.locator("#campo-nome"), "Giulia")
    scrivi(app.locator("#campo-cognome"), "Neri")
    scrivi(app.locator("#campo-telefono"), "333 765 4321")
    scrivi(app.locator("#campo-email"), "giulia.neri@example.com")
    scrivi(app.locator("#campo-password"), "pilates2026")
    tocca(app.locator("#campo-privacy"), 0.4)
    tocca(app.locator('button[type="submit"]'), 1.0)

    # 3. Guided intro
    app.locator(".benvenuto").wait_for(timeout=20000)
    didascalia("Welcome", "A short guided tour explains how it works.", 2.0)
    avanti = app.locator(".benvenuto .comandi .bottone")
    for _ in range(3):
        tocca(avanti, 2.2)
    tocca(app.locator(".benvenuto .salta"), 1.0)

    # 4. Booking
    app.locator(".striscia .giorno").first.wait_for(timeout=20000)
    COPERTINA[0] = time.monotonic() - AVVIO
    didascalia("Book", "Pick a day in the week strip, or switch to the full month.", 1.0)
    tocca(app.locator(f'.striscia [data-giorno="{giorno_prenota}"]'), 1.4)
    tocca(app.locator('[data-vista="mese"]'), 1.6)
    tocca(app.locator(f'.cella[data-giorno="{giorno_prenota}"]'), 1.2)
    didascalia("Live availability", "Each dot is a reformer. Empty means free.", 2.2)
    libere = app.locator(".lezione.libera, .lezione.ultimo")
    tocca(libere.first, 1.4)
    didascalia("One tap", "See the three reformers, the instructor and the cancellation window.", 2.2)
    tocca(app.locator(".foglio .bottone.prenota"), 1.6)
    didascalia("Booked", "Instant confirmation. A reminder goes out the day before.", 2.6)
    tocca(app.locator(".foglio .conferma .bottone"), 0.8)

    # 5. Waitlist
    tocca(app.locator('[data-vista="settimana"]'), 0.8)
    tocca(app.locator(f'.striscia [data-giorno="{giorno_pieno}"]'), 1.2)
    didascalia("Waitlist", "Class full? Join the waitlist: if someone cancels, you're in automatically.", 1.2)
    tocca(app.locator(".lezione.piena").first, 1.4)
    tocca(app.locator(".foglio .bottone.attesa"), 2.4)

    # 6. Cancelling
    tocca(app.locator('.tab a[href="#/mie"]'), 0.8)
    didascalia("Cancel", "Cancel up to 12 hours before: the lesson goes back to the package.", 1.2)
    tocca(app.locator(".lezione.mia").first, 1.4)
    tocca(app.locator(".foglio .bottone.secondario"), 1.0)
    pausa(1.6)

    # 7. Package
    tocca(app.locator('.tab a[href="#/pacchetto"]'), 0.8)
    didascalia("Package", "Remaining lessons at a glance. Payment stays in the studio.", 3.0)

    # 8. Studio side
    esci()
    didascalia("Studio dashboard", "The instructors get their own back office, in the same app.", 1.4)
    scrivi(app.locator("#campo-email"), "greta.lorenzetti@icloud.com")
    scrivi(app.locator("#campo-password"), "demo1234")
    tocca(app.locator('button[type="submit"]'), 1.6)
    app.locator(".registro").first.wait_for(timeout=20000)
    didascalia("Today", "Who is coming, who is on the waitlist, attendance in one tap.", 1.4)
    tocca(app.locator(".registro .presenza .si").first, 1.2)
    tocca(app.locator(".registro .presenza .si").nth(1), 1.6)

    tocca(app.locator('.tab a[href="#/studio/clienti"]'), 0.8)
    didascalia("Clients", "Lessons are paid in the studio: the instructors top up each package.", 1.0)
    scrivi(app.locator("#cerca-cliente"), "Giulia")
    pausa(0.8)
    tocca(app.locator(".riga-cliente", has_text="Giulia").first, 1.2)
    tocca(app.locator("button.chip", has_text="+10"), 0.8)
    scrivi(app.locator("#nota-saldo"), "10-lesson package, paid in studio")
    tocca(app.locator(".riquadro.carica .bottone.largo"), 2.0)

    tocca(app.locator('.tab a[href="#/studio/settimana"]'), 1.0)
    didascalia("Full control", "Rename classes, add or remove clients, open an extra class or cancel with an automatic notice.", 1.2)
    tocca(app.locator(".riga-studio:not(.passata):not(.aggiungi-lezione)").nth(3), 2.0)
    pausa(2.4)
    tocca(app.locator(".foglio .tondo"), 0.8)

    # 9. Closing card
    COPIONE.append((time.monotonic() - AVVIO, "End", "RE FORMER — designed, built and deployed end to end."))
    pagina.evaluate("() => finale()")
    pausa(5.0)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--veloce", action="store_true")
    a = p.parse_args()
    global LENTO, AVVIO
    if a.veloce:
        LENTO = 0.5

    from playwright.sync_api import sync_playwright

    USCITA.mkdir(exist_ok=True)
    for coda in ("", "-shm", "-wal"):
        (USCITA / f"video.db{coda}").unlink(missing_ok=True)
    subprocess.run([sys.executable, "-m", "reformer.db.init_db"], cwd=RADICE, env=ambiente(), check=True, capture_output=True)
    processi = [
        subprocess.Popen([sys.executable, "-m", "uvicorn", "reformer.main:app", "--host", "127.0.0.1", "--port", str(PORTA_APP), "--log-level", "warning"],
                         cwd=RADICE, env=ambiente(), stdout=open(USCITA / "server.log", "w"), stderr=subprocess.STDOUT),
        subprocess.Popen([sys.executable, "-m", "http.server", str(PORTA_PALCO), "--bind", "127.0.0.1"],
                         cwd=RADICE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
    ]
    try:
        if not (porta_pronta(PORTA_APP) and porta_pronta(PORTA_PALCO)):
            raise RuntimeError("server or stage not answering")
        giorno_prenota, giorno_pieno = prepara_dati_con_server()
        print("Booking day:", giorno_prenota, "· full day:", giorno_pieno)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROMIUM)
            contesto = browser.new_context(viewport={"width": LARGO, "height": ALTO},
                                           record_video_dir=str(USCITA), record_video_size={"width": LARGO, "height": ALTO})
            pagina = contesto.new_page()
            AVVIO = time.monotonic()
            pagina.goto(f"http://127.0.0.1:{PORTA_PALCO}/reformer/video/palco.html", wait_until="networkidle")
            pausa(1.2)
            gira(pagina, giorno_prenota, giorno_pieno)
            percorso = pagina.video.path()
            contesto.close()
            browser.close()
        webm = Path(percorso)
        mp4 = USCITA / "video.mp4"
        in_mp4(webm, mp4)
        copertina(mp4, USCITA / "copertina.jpg", COPERTINA[0] + 3.0)
        scrivi_copione(USCITA / "copione.txt")
        webm.unlink(missing_ok=True)
        print(f"Video:  {mp4}  ({mp4.stat().st_size // 1024} kB)")
    finally:
        for pr in processi:
            pr.terminate()
        for pr in processi:
            pr.wait(timeout=10)
    return 0


def prepara_dati_con_server() -> tuple[str, str]:
    """Seeds demo data (needs the server already running on an empty DB)."""
    subprocess.run([sys.executable, "-m", "reformer.scripts.dati_esempio"], cwd=RADICE, env=ambiente(), check=True, capture_output=True)
    return _scegli_giorni()


def _scegli_giorni() -> tuple[str, str]:
    riempitrici = []
    for i, (nome, cognome) in enumerate([("Elena", "Costa"), ("Marta", "Gentile"), ("Irene", "Sala")]):
        r = chiama("POST", "/api/auth/registrati", {
            "nome": nome, "cognome": cognome, "telefono": f"340 100 20{i}0",
            "email": f"{nome.lower()}.{cognome.lower()}@example.com", "password": "pilates2026", "privacy": True,
        })
        riempitrici.append(r["token"])
    oggi = datetime.now(ROMA).date()
    lezioni = chiama("GET", f"/api/lezioni?da={oggi}&giorni=20", token=riempitrici[0])
    per_giorno: dict[date, list] = {}
    for l in lezioni:
        if l["passata"] or not l["prenotabile"]:
            continue
        per_giorno.setdefault(datetime.fromisoformat(l["inizio"]).astimezone(ROMA).date(), []).append(l)
    giorni = sorted(per_giorno)
    prenota = next(d for d in giorni if d >= oggi + timedelta(days=2))
    piena = next(d for d in giorni if d >= prenota + timedelta(days=2))
    for token in riempitrici:
        chiama("POST", f"/api/lezioni/{per_giorno[piena][0]['id']}/prenota", token=token)
    return prenota.isoformat(), piena.isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
