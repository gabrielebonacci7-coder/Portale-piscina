"""Gira il video di presentazione dell'app per le clienti di Pilates G&E.

    python pilates/video/gira.py            # video completo
    python pilates/video/gira.py --veloce   # pause dimezzate, per provare i tagli

Come per la piscina di Ciampino, non è un montaggio: guida il **prototipo
vero** dentro un telefono e riprende lo schermo. Se cambia un testo, un
colore o arrivano gli avatar, il video si rifà lanciando di nuovo questo
comando.

Esce in verticale 1080×1920 e senza voce: parlano i fumetti di Greta ed
Elisa e le didascalie sotto il telefono. I file finiscono in
pilates/video/uscita/: video.mp4, copertina.jpg e copione.txt.

Serve Playwright (pip install playwright) e ffmpeg.
"""

import argparse
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

PILATES = Path(__file__).resolve().parents[1]
USCITA = Path(__file__).resolve().parent / "uscita"
CHROMIUM = "/opt/pw-browsers/chromium"
PORTA = 8212

LARGO, ALTO = 1080, 1920

# Un lunedì mattina: le lezioni di oggi non si possono più disdire (mancano
# meno di 12 ore), quelle da domani sì. Così il video viene sempre uguale.
ORA = "2026-10-12T09:00"

LENTO = 1.0
COPIONE: list[tuple[float, str, str]] = []
AVVIO = 0.0


def pausa(secondi: float) -> None:
    time.sleep(secondi * LENTO)


def porta_pronta(porta: int, secondi: int = 15) -> bool:
    scadenza = time.time() + secondi
    while time.time() < scadenza:
        with socket.socket() as s:
            s.settimeout(0.4)
            if s.connect_ex(("127.0.0.1", porta)) == 0:
                return True
        time.sleep(0.2)
    return False


def in_mp4(webm: Path, mp4: Path) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    subprocess.run(
        [ffmpeg, "-y", "-i", str(webm),
         "-c:v", "libx264", "-preset", "slow", "-crf", "20",
         "-pix_fmt", "yuv420p",       # senza, molti telefoni non lo aprono
         "-movflags", "+faststart",   # parte subito anche mentre si scarica
         "-r", "30", str(mp4)],
        check=True, capture_output=True,
    )


def copertina(mp4: Path, jpg: Path, secondo: float) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    subprocess.run(
        [ffmpeg, "-y", "-ss", str(secondo), "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(jpg)],
        check=True, capture_output=True,
    )


def scrivi_copione(percorso: Path) -> None:
    righe = ["Copione del video — quando compare ogni frase", ""]
    for istante, passo, frase in COPIONE:
        minuti, secondi = divmod(istante, 60)
        righe.append(f"{int(minuti):02d}:{secondi:05.2f}  [{passo}] {frase}")
    percorso.write_text("\n".join(righe) + "\n", encoding="utf-8")


# -------------------------------------------------------------------- il video
def gira(pagina) -> None:
    """La sceneggiatura, scena per scena.

    È pensata per chi è già cliente dello studio: non deve convincere, deve
    far vedere che è facile. Registrarsi, prenotare, la lista d'attesa,
    disdire, il pacchetto, e a chi scrivere.
    """
    app = pagina.frame_locator("#app")

    def didascalia(passo, frase, attesa=2.6):
        COPIONE.append((time.monotonic() - AVVIO, passo, frase))
        pagina.evaluate("([p, f]) => didascalia(p, f)", [passo, frase])
        pausa(attesa)

    def tocca(elemento, attesa=1.1):
        """Fa vedere il dito e poi tocca davvero."""
        elemento.wait_for(timeout=15000)
        elemento.scroll_into_view_if_needed()
        r = elemento.bounding_box()
        if r:
            pagina.evaluate("([x, y]) => tocco(x, y)", [r["x"] + r["width"] / 2, r["y"] + r["height"] / 2])
            pausa(0.35)
        elemento.click()
        pausa(attesa)

    def scrivi(campo, testo, attesa=0.25):
        campo.click()
        campo.type(testo, delay=28 * LENTO)
        pausa(attesa)

    # --- 1. La novità ---
    app.locator(".accesso").wait_for(timeout=20000)
    didascalia("Novità", "Da oggi le lezioni si prenotano dall'app.", 2.8)

    # --- 2. Registrarsi, una volta sola ---
    tocca(app.locator('a[href="#/registrati"]'), 0.6)
    didascalia("Un minuto", "Ti registri una volta sola, con nome, telefono ed email.", 0.6)
    scrivi(app.locator('input[name="nome"]'), "Sofia")
    scrivi(app.locator('input[name="cognome"]'), "Marini")
    scrivi(app.locator('input[name="telefono"]'), "333 123 4567")
    scrivi(app.locator('input[name="email"]'), "sofia.marini@email.it")
    scrivi(app.locator('input[name="password"]'), "pilates2026")
    tocca(app.locator('input[name="privacy"]'), 0.4)
    tocca(app.locator('button[type="submit"]'), 1.0)

    # --- 3. Greta ed Elisa spiegano ---
    didascalia("Benvenuta", "Greta ed Elisa ti spiegano come funziona.", 2.6)
    avanti = app.locator(".benvenuto .comandi .bottone")
    for i in range(7):
        tocca(avanti, 3.4 if i else 2.4)
    pausa(0.6)
    tocca(avanti, 1.2)  # "Prenota la prima lezione"

    # --- 4. Prenotare ---
    didascalia("Prenotare", "Scegli il giorno: sotto ci sono le lezioni, con chi le tiene.", 1.0)
    tocca(app.locator('[data-giorno="2026-10-14"]'), 1.6)
    didascalia("I pallini", "Ogni pallino è un reformer: vuoto vuol dire libero.", 2.0)
    libera = app.locator(".lezione.libera, .lezione.ultimo").first
    tocca(libera, 1.6)
    didascalia("Un tocco", "Vedi i 3 reformer, e quando puoi ancora disdire.", 1.8)
    tocca(app.locator(".foglio .bottone.prenota"), 1.6)
    didascalia("Fatto", "Prenotata! Il giorno prima arriva il promemoria.", 2.4)
    tocca(app.locator(".foglio .conferma .bottone"), 0.8)

    # --- 5. Lezione piena: lista d'attesa ---
    giorni = app.locator(".striscia .giorno")
    for i in range(giorni.count()):
        g = giorni.nth(i)
        if g.get_attribute("data-giorno") <= "2026-10-14":
            continue
        tocca(g, 0.6)
        if app.locator(".lezione.piena").count():
            break
    didascalia("Lista d'attesa", "Lezione piena? Mettiti in lista: se si libera un posto, entri tu.", 1.2)
    tocca(app.locator(".lezione.piena").first, 1.4)
    tocca(app.locator(".foglio .bottone.attesa"), 2.4)

    # --- 6. Disdire ---
    tocca(app.locator('.tab a[href="#/mie"]'), 0.6)
    didascalia("Disdire", "Non puoi venire? Disdici fino a 12 ore prima.", 1.0)
    tocca(app.locator(".lezione.mia").first, 1.4)
    tocca(app.locator(".foglio .bottone.secondario"), 1.0)
    didascalia("Disdire", "La lezione torna nel tuo pacchetto, e il posto va a chi aspetta.", 2.4)

    # --- 7. Il pacchetto si paga in studio ---
    tocca(app.locator('.tab a[href="#/pacchetto"]'), 0.6)
    didascalia("Pagamento", "Si paga in studio, come sempre.", 1.8)
    pagina.frame_locator("#app").locator("body").evaluate("() => window.prototipo.simulaPagamento()")
    didascalia("Pagamento", "Greta o Elisa caricano il pacchetto: qui vedi le lezioni che ti restano.", 3.2)

    # --- 8. Contatti ---
    tocca(app.locator('.tab a[href="#/contatti"]'), 0.6)
    didascalia("Contatti", "Per qualsiasi cosa, un tocco e scrivi a Greta o a Elisa.", 3.0)
    didascalia("Sul telefono", "Mettila nella schermata Home: si apre come un'app.", 0.6)
    pagina.mouse.move(LARGO / 2, 900)
    for _ in range(4):
        pagina.mouse.wheel(0, 300)
        pausa(0.5)
    pausa(2.0)

    # --- 9. Cartello finale ---
    COPIONE.append((time.monotonic() - AVVIO, "Finale", "Pilates G&E — ti aspettiamo sul reformer."))
    pagina.evaluate("() => finale()")
    pausa(4.2)


def main() -> int:
    lettore = argparse.ArgumentParser(description=__doc__)
    lettore.add_argument("--veloce", action="store_true", help="pause dimezzate")
    argomenti = lettore.parse_args()

    global LENTO, AVVIO
    if argomenti.veloce:
        LENTO = 0.5

    from playwright.sync_api import sync_playwright

    USCITA.mkdir(exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORTA), "--bind", "127.0.0.1"],
        cwd=PILATES, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        if not porta_pronta(PORTA):
            raise RuntimeError("il server del prototipo non risponde")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROMIUM)
            # Contesto nuovo = telefono nuovo: niente dati salvati, l'app si
            # apre come la vede una cliente la prima volta.
            contesto = browser.new_context(
                viewport={"width": LARGO, "height": ALTO},
                record_video_dir=str(USCITA),
                record_video_size={"width": LARGO, "height": ALTO},
            )
            pagina = contesto.new_page()
            AVVIO = time.monotonic()
            pagina.goto(
                f"http://127.0.0.1:{PORTA}/video/palco.html?app=" + f"%3Fora%3D{ORA}%26video%3D1",
                wait_until="networkidle",
            )
            pausa(1.0)
            gira(pagina)
            percorso = pagina.video.path()
            contesto.close()
            browser.close()

        webm = Path(percorso)
        mp4 = USCITA / "video.mp4"
        in_mp4(webm, mp4)
        copertina(mp4, USCITA / "copertina.jpg", secondo=15.39)
        scrivi_copione(USCITA / "copione.txt")
        webm.unlink(missing_ok=True)
        print(f"Video:     {mp4}  ({mp4.stat().st_size // 1024} kB)")
        print(f"Copertina: {USCITA / 'copertina.jpg'}")
        print(f"Copione:   {USCITA / 'copione.txt'}")
    finally:
        server.terminate()
        server.wait(timeout=10)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
