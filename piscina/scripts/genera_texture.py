"""Disegna le texture della mappa: erba, acqua e pavimento del solarium.

    python -m piscina.scripts.genera_texture

Sono tre piastrelle da 256 pixel che si ripetono senza giunture, e la mappa le
usa come sfondo. Il perché di questo giro: la stessa grana fatta con i filtri
dell'SVG (feTurbulence) si ricalcola a ogni zoom e su un telefono di tre anni
fa la mappa diventa una diapositiva. Una piastrella disegnata una volta sola
si ripete senza costare niente.

Le piastrelle sono continue: ogni macchia viene disegnata nove volte, anche
appena fuori dai bordi, così quello che esce da un lato rientra dall'altro e
la ripetizione non lascia il reticolo.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

CARTELLA = Path(__file__).resolve().parents[1] / "web" / "immagini"
LATO = 256


def _sfuma(img: Image.Image, raggio: float) -> Image.Image:
    """Sfoca senza rompere la continuità.

    La sfocatura di Pillow non sa che la piastrella si ripete: sui bordi
    inventa, e ripetendola si vede la riga. Qui si sfoca una copia affiancata
    nove volte e si ritaglia quella in mezzo.
    """
    lato = img.width
    grande = Image.new(img.mode, (lato * 3, lato * 3))
    for dx in range(3):
        for dy in range(3):
            grande.paste(img, (dx * lato, dy * lato))
    grande = grande.filter(ImageFilter.GaussianBlur(raggio))
    return grande.crop((lato, lato, lato * 2, lato * 2))


def _nove_volte(disegna, lato: int = LATO) -> None:
    """Ripete il disegno anche sui bordi, per la continuità della piastrella."""
    for dx in (-lato, 0, lato):
        for dy in (-lato, 0, lato):
            disegna(dx, dy)


def erba() -> Image.Image:
    caso = random.Random(7)
    tela = Image.new("RGB", (LATO, LATO), (124, 158, 92))
    matita = ImageDraw.Draw(tela)

    # Chiazze larghe: il prato non è di un verde solo.
    for _ in range(70):
        x, y = caso.uniform(0, LATO), caso.uniform(0, LATO)
        r = caso.uniform(14, 40)
        tono = caso.choice([(112, 146, 82), (136, 170, 100), (118, 152, 86)])
        _nove_volte(lambda dx, dy, x=x, y=y, r=r, tono=tono: matita.ellipse(
            [x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=tono
        ))
    tela = _sfuma(tela, 6)

    # Fili d'erba: trattini corti, tutti più o meno nella stessa direzione.
    matita = ImageDraw.Draw(tela)
    for _ in range(1400):
        x, y = caso.uniform(0, LATO), caso.uniform(0, LATO)
        lung = caso.uniform(3, 7)
        ang = caso.uniform(-0.5, 0.5) - math.pi / 2
        chiaro = caso.random() < 0.5
        tono = (142, 176, 104) if chiaro else (104, 138, 76)
        _nove_volte(lambda dx, dy, x=x, y=y, l=lung, a=ang, t=tono: matita.line(
            [x + dx, y + dy, x + dx + l * math.cos(a), y + dy + l * math.sin(a)],
            fill=t, width=1,
        ))
    return _sfuma(tela, 0.4)


def acqua() -> Image.Image:
    caso = random.Random(11)
    tela = Image.new("RGB", (LATO, LATO), (36, 150, 200))
    matita = ImageDraw.Draw(tela)

    for _ in range(40):
        x, y = caso.uniform(0, LATO), caso.uniform(0, LATO)
        r = caso.uniform(20, 55)
        tono = caso.choice([(28, 134, 186), (52, 170, 214)])
        _nove_volte(lambda dx, dy, x=x, y=y, r=r, t=tono: matita.ellipse(
            [x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=t
        ))
    tela = _sfuma(tela, 9)

    # I riflessi del sole sul fondo: linee chiare che si intrecciano.
    riflessi = Image.new("L", (LATO, LATO), 0)
    matita = ImageDraw.Draw(riflessi)
    for _ in range(48):
        x, y = caso.uniform(0, LATO), caso.uniform(0, LATO)
        punti = [(x, y)]
        ang = caso.uniform(0, 2 * math.pi)
        for _ in range(caso.randint(4, 9)):
            ang += caso.uniform(-0.9, 0.9)
            passo = caso.uniform(6, 14)
            punti.append((punti[-1][0] + passo * math.cos(ang), punti[-1][1] + passo * math.sin(ang)))
        _nove_volte(lambda dx, dy, p=punti: matita.line(
            [(px + dx, py + dy) for px, py in p], fill=190, width=caso.randint(3, 6), joint="curve"
        ))
    riflessi = _sfuma(riflessi, 3.4)

    chiaro = Image.new("RGB", (LATO, LATO), (198, 236, 250))
    return Image.composite(chiaro, tela, riflessi.point(lambda v: int(v * 0.34)))


def pavimento() -> Image.Image:
    caso = random.Random(13)
    tela = Image.new("RGB", (LATO, LATO), (233, 220, 195))
    matita = ImageDraw.Draw(tela)

    # Granulosità della pietra.
    for _ in range(9000):
        x, y = caso.randrange(LATO), caso.randrange(LATO)
        v = caso.randint(-12, 12)
        base = tela.getpixel((x, y))
        matita.point((x, y), fill=tuple(max(0, min(255, c + v)) for c in base))
    tela = _sfuma(tela, 0.6)

    # Le fughe fra le mattonelle: due righe per lato, sottili e chiare.
    matita = ImageDraw.Draw(tela)
    for i in (0, LATO // 2):
        matita.line([i, 0, i, LATO], fill=(222, 207, 178), width=2)
        matita.line([0, i, LATO, i], fill=(222, 207, 178), width=2)
    return tela


def main() -> None:
    CARTELLA.mkdir(parents=True, exist_ok=True)
    for nome, disegno in (("erba", erba()), ("acqua", acqua()), ("pavimento", pavimento())):
        percorso = CARTELLA / f"texture-{nome}.webp"
        disegno.save(percorso, quality=82, method=6)
        print(f"{percorso.name}: {percorso.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
