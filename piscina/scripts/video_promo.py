"""Gira il video di presentazione dell'app.

    python -m piscina.scripts.video_promo             # video completo
    python -m piscina.scripts.video_promo --veloce    # pause dimezzate, per provare i tagli

Non è un montaggio di figurine: guida l'**applicazione vera** dentro un
telefono e riprende quello che succede sullo schermo. Se domani cambia il
listino o la disposizione degli ombrelloni, il video si rifà lanciando di
nuovo questo comando.

Esce in verticale 1080×1920, la misura di Instagram, TikTok e WhatsApp, e
senza audio: la musica o la voce si aggiungono dopo, sopra le didascalie che
scandiscono già il ritmo.

I file finiscono in `demo/`: video.mp4 e copertina.jpg.
"""

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
USCITA = RADICE / "demo"
CHROMIUM = "/opt/pw-browsers/chromium"

PORTA_APP = 8102
PORTA_PALCO = 8103

DB_VIDEO = RADICE / "piscina_video.db"

# Misura del video e del telefono dentro al palco.
LARGO, ALTO = 1080, 1920

# Ritmo: il tempo di leggere una didascalia senza mettere in pausa.
LENTO = 1.0

# Quando compare ogni didascalia, per chi poi ci mette la voce sopra. I tempi
# si contano da quando parte la registrazione, non da quando parte la scena:
# è il minutaggio del file, quello che serve al montaggio.
COPIONE: list[tuple[float, str, str]] = []
AVVIO_VIDEO = 0.0


def pausa(secondi: float) -> None:
    time.sleep(secondi * LENTO)


# ---------------------------------------------------------------- preparazione
def _ambiente() -> dict:
    return {
        **os.environ,
        "PISCINA_DATABASE_URL": f"sqlite:///{DB_VIDEO}",
        "PISCINA_EMAIL_SMTP_HOST": "",
        "PISCINA_EMAIL_STAFF": "",
    }


def prepara_dati() -> None:
    """Un database solo per il video: quello vero non si tocca."""
    for coda in ("", "-shm", "-wal"):
        Path(f"{DB_VIDEO}{coda}").unlink(missing_ok=True)
    for modulo in ("piscina.db.init_db", "piscina.scripts.dati_esempio"):
        subprocess.run(
            [sys.executable, "-m", modulo],
            cwd=RADICE, env=_ambiente(), check=True, capture_output=True,
        )


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
    USCITA.mkdir(exist_ok=True)
    processi = [
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "piscina.main:app",
             "--host", "127.0.0.1", "--port", str(PORTA_APP), "--log-level", "warning"],
            cwd=RADICE, env=_ambiente(),
            stdout=open(USCITA / "server.log", "w"), stderr=subprocess.STDOUT,
        ),
        subprocess.Popen(
            [sys.executable, "-m", "http.server", str(PORTA_PALCO), "--bind", "127.0.0.1"],
            cwd=Path(__file__).resolve().parent / "demo",
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ),
    ]
    for porta in (PORTA_APP, PORTA_PALCO):
        if not porta_pronta(porta):
            raise RuntimeError(f"il servizio sulla porta {porta} non risponde")
    return processi


# ------------------------------------------------------------------ montaggio
def in_mp4(webm: Path, mp4: Path) -> None:
    import imageio_ffmpeg

    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(webm),
         # crf basso: lo sfondo è una sfumatura scura, e comprimendola troppo si
         # vede a strisce.
         "-c:v", "libx264", "-preset", "slow", "-crf", "19",
         "-pix_fmt", "yuv420p",       # senza, molti lettori non lo aprono
         "-movflags", "+faststart",   # parte subito anche mentre si scarica
         "-r", "30", str(mp4)],
        check=True, capture_output=True,
    )


def scrivi_copione(percorso: Path) -> None:
    """Il minutaggio delle didascalie.

    Serve a chi ci mette la voce o la musica sopra: le frasi sono già scritte
    e il momento in cui compaiono è questo, al decimo di secondo.
    """
    righe = ["Copione del video — quando compare ogni frase", ""]
    for istante, passo, frase in COPIONE:
        minuti, secondi = divmod(istante, 60)
        righe.append(f"{int(minuti):02d}:{secondi:05.2f}  [{passo}] {frase}")
    percorso.write_text("\n".join(righe) + "\n", encoding="utf-8")


def copertina(mp4: Path, jpg: Path, secondo: float) -> None:
    import imageio_ffmpeg

    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-ss", str(secondo), "-i", str(mp4),
         "-frames:v", "1", "-q:v", "3", str(jpg)],
        check=True, capture_output=True,
    )


# -------------------------------------------------------------------- il video
def gira(pagina) -> None:
    """La sequenza, scena per scena. È questa la sceneggiatura.

    L'ordine racconta come si usa davvero l'app: si guarda la mappa, si
    controllano i prezzi, si sceglie il posto, si conferma. Finisce sul codice
    di prenotazione perché è lì che il cliente capisce di avercela fatta.
    """
    app = pagina.frame_locator("#app")

    def didascalia(passo, frase, attesa=2.8):
        COPIONE.append((time.monotonic() - AVVIO_VIDEO, passo, frase))
        pagina.evaluate("([p, f]) => didascalia(p, f)", [passo, frase])
        pausa(attesa)

    def tocca(elemento, attesa=1.2):
        """Fa vedere il dito e poi tocca davvero."""
        elemento.wait_for(timeout=15000)
        riquadro = elemento.bounding_box()
        if riquadro:
            pagina.evaluate(
                "([x, y]) => tocco(x, y)",
                [riquadro["x"] + riquadro["width"] / 2, riquadro["y"] + riquadro["height"] / 2],
            )
            pausa(0.35)
        elemento.click()
        pausa(attesa)

    def scrivi(campo, testo, attesa=0.35):
        campo.click()
        campo.type(testo, delay=30 * LENTO)  # a mano, non incollato
        pausa(attesa)

    # --- 1. L'app si apre: c'è l'omino che dà il benvenuto ---
    app.locator(".benvenuto").wait_for(timeout=20000)
    didascalia("Il portale", "Il nuovo portale di prenotazione della piscina comunale.", 2.6)

    # --- 2. Il problema che risolve ---
    tocca(app.locator(".benvenuto .salta"), 0.7)
    app.locator(".mappa-scorri svg").wait_for(timeout=20000)
    didascalia(
        "Il problema",
        "Quante volte sei arrivato in piscina e hai trovato tutto pieno?",
        2.4,
    )

    # --- 3. La mappa, e cosa dicono i colori ---
    didascalia("La mappa", "Il solarium visto dall'alto: in verde quello che è libero.", 2.2)

    # --- 4. Anche mezza giornata ---
    didascalia("Mezza giornata", "Giornata intera, solo mattina o solo pomeriggio.", 1.0)
    tocca(app.locator(".segmentato button").nth(1), 1.7)
    tocca(app.locator(".segmentato button").nth(0), 1.0)

    # --- 5. I prezzi, scritti ---
    tocca(app.locator('.tab a[href="#/prezzi"]'), 0.6)
    didascalia("Prezzi chiari", "Tutti i pacchetti e le tariffe, sempre sott'occhio.", 1.1)
    for _ in range(3):
        pagina.mouse.move(LARGO / 2, 900)
        pagina.mouse.wheel(0, 280)
        pausa(0.55)
    pausa(0.5)

    # --- 6. Due tocchi: il posto è scelto ---
    tocca(app.locator('.tab a[href="#/prenota"]'), 0.8)
    didascalia("Due tocchi", "Scegli ombrellone e lettini esattamente dove vuoi tu.", 1.1)
    tocca(app.locator('[data-codice="A9"]'), 1.0)
    tocca(app.locator(".foglio .pacchetto").nth(3), 0.7)   # ombrellone + 3 lettini
    tocca(app.locator(".foglio .bottone.largo").first, 1.2)

    # --- 7. Si conferma, e si paga in cassa ---
    tocca(app.locator(".scheda .bottone.largo").last, 0.8)
    didascalia("Un minuto", "Lasci un contatto, e paghi in cassa quando arrivi.", 0.9)
    scrivi(app.locator('input[name="nome"]'), "Marco Rossi")
    scrivi(app.locator('input[name="telefono"]'), "333 1234567")
    scrivi(app.locator('input[name="email"]'), "marco.rossi@example.com", 0.6)
    tocca(app.locator('.foglio button[type="submit"]'), 2.0)

    # --- 8. L'omino ringrazia, poi arriva il codice ---
    didascalia("Fatto", "La postazione è tua. Il codice serve solo in cassa.", 0.9)
    tocca(app.locator(".benvenuto .avanti"), 0.8)
    tocca(app.locator(".benvenuto .avanti"), 2.2)

    # --- 9. Cartello finale ---
    COPIONE.append((time.monotonic() - AVVIO_VIDEO, "Finale", "Piscina Comunale di Ciampino — prenota il tuo posto."))
    pagina.evaluate("() => finale()")
    pausa(3.6)


def main() -> int:
    lettore = argparse.ArgumentParser(description=__doc__)
    lettore.add_argument("--veloce", action="store_true", help="pause dimezzate")
    argomenti = lettore.parse_args()

    global LENTO
    if argomenti.veloce:
        LENTO = 0.5

    from playwright.sync_api import sync_playwright

    prepara_dati()
    processi = avvia_servizi()
    USCITA.mkdir(exist_ok=True)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROMIUM)
            contesto = browser.new_context(
                viewport={"width": LARGO, "height": ALTO},
                # Contesto nuovo = localStorage vuoto: l'app si apre davvero
                # come si apre la prima volta, con il benvenuto.
                record_video_dir=str(USCITA),
                record_video_size={"width": LARGO, "height": ALTO},
            )
            pagina = contesto.new_page()
            global AVVIO_VIDEO
            AVVIO_VIDEO = time.monotonic()  # da qui in poi la telecamera gira
            pagina.goto(
                f"http://127.0.0.1:{PORTA_PALCO}/palco.html"
                f"?app=http://127.0.0.1:{PORTA_APP}",
                wait_until="networkidle",
            )
            pausa(1.2)
            gira(pagina)
            percorso = pagina.video.path()
            contesto.close()   # il webm si chiude qui
            browser.close()

        webm = Path(percorso)
        mp4 = USCITA / "video.mp4"
        in_mp4(webm, mp4)
        copertina(mp4, USCITA / "copertina.jpg", secondo=11.0)
        scrivi_copione(USCITA / "copione.txt")
        webm.unlink(missing_ok=True)

        print(f"Video: {mp4}  ({mp4.stat().st_size // 1024} kB)")
        print(f"Copertina: {USCITA / 'copertina.jpg'}")
        print(f"Copione:   {USCITA / 'copione.txt'}")
    finally:
        for processo in processi:
            processo.terminate()
        for processo in processi:
            processo.wait(timeout=10)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
