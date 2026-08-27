"""Disegna le icone PNG dell'app.

    python -m piscina.scripts.genera_icone

Sono lo stesso ombrellone dell'icona SVG, ridisegnato con Pillow perché il
manifest vuole dei PNG di misura fissa e iOS non legge l'SVG. Si rigenerano
solo quando cambia il disegno: i file finiscono in piscina/web/icone/.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

CARTELLA = Path(__file__).resolve().parents[1] / "web" / "icone"

ACQUA_CHIARA = (63, 179, 224)
ACQUA_SCURA = (10, 99, 146)
BIANCO = (255, 255, 255)
GIALLO = (242, 177, 52)

# Si disegna sempre a 1024 e si riduce: gli spigoli vengono lisci senza
# scomodare l'antialiasing a mano.
LATO = 1024


def _sfondo(disegno: ImageDraw.ImageDraw, raggio: int) -> None:
    """Sfumatura dall'azzurro chiaro in alto al blu profondo in basso."""
    for y in range(LATO):
        t = y / LATO
        colore = tuple(
            round(ACQUA_CHIARA[i] + (ACQUA_SCURA[i] - ACQUA_CHIARA[i]) * t) for i in range(3)
        )
        disegno.line([(0, y), (LATO, y)], fill=colore)

    if raggio:
        # Gli angoli si tagliano con una maschera, applicata da chi chiama.
        pass


def _ombrellone(strato: Image.Image) -> None:
    disegno = ImageDraw.Draw(strato)
    s = LATO / 512  # il disegno è pensato su 512, come l'SVG

    def p(*coppie):
        return [(x * s, y * s) for x, y in coppie]

    # Il telo: mezza ellisse bianca, poi due spicchi gialli ai lati e uno al centro.
    disegno.pieslice([104 * s, 116 * s, 408 * s, 420 * s], 180, 360, fill=BIANCO)
    disegno.polygon(p((256, 116), (204, 268), (256, 268)), fill=GIALLO)
    disegno.polygon(p((104, 268), (172, 268), (204, 125)), fill=GIALLO)
    disegno.polygon(p((408, 268), (340, 268), (308, 125)), fill=GIALLO)

    # Il palo.
    disegno.rounded_rectangle([245 * s, 262 * s, 267 * s, 412 * s], radius=11 * s, fill=BIANCO)

    # Due onde. Si timbrano cerchietti lungo la curva invece di tracciare una
    # linea: Pillow non sa arrotondare i giunti, e una linea spessa piegata
    # viene fuori tutta seghettata.
    for y, spessore, velo in ((400, 18, 150), (448, 18, 82)):
        raggio = spessore * s / 2
        # Ogni onda si disegna piena su un suo strato e si sfuma alla fine:
        # timbrando cerchi semitrasparenti uno sull'altro, le sovrapposizioni
        # verrebbero più scure e l'onda a chiazze.
        onda = Image.new("RGBA", (LATO, LATO), (0, 0, 0, 0))
        matita = ImageDraw.Draw(onda)
        for i in range(0, 421):
            cx = (52 + i) * s
            cy = (y + 13 * math.sin(i / 50 * math.pi)) * s
            matita.ellipse([cx - raggio, cy - raggio, cx + raggio, cy + raggio], fill=BIANCO)
        onda.putalpha(onda.getchannel("A").point(lambda a, v=velo: a * v // 255))
        strato.alpha_composite(onda)


def _tela(raggio_angoli: int) -> Image.Image:
    base = Image.new("RGB", (LATO, LATO), ACQUA_SCURA)
    _sfondo(ImageDraw.Draw(base), raggio_angoli)

    strato = Image.new("RGBA", (LATO, LATO), (0, 0, 0, 0))
    _ombrellone(strato)
    base = Image.alpha_composite(base.convert("RGBA"), strato)

    if raggio_angoli:
        maschera = Image.new("L", (LATO, LATO), 0)
        ImageDraw.Draw(maschera).rounded_rectangle(
            [0, 0, LATO - 1, LATO - 1], radius=raggio_angoli, fill=255
        )
        base.putalpha(maschera)
    return base


def main() -> None:
    CARTELLA.mkdir(parents=True, exist_ok=True)

    # Icona normale: angoli arrotondati come le icone di sistema.
    normale = _tela(raggio_angoli=round(LATO * 0.226))
    for misura in (192, 512, 180):
        normale.resize((misura, misura), Image.LANCZOS).save(CARTELLA / f"icona-{misura}.png")

    # Icona mascherabile: quadrata piena e con più aria attorno, perché
    # Android la ritaglia come vuole (cerchio, goccia, quadrato stondato).
    piena = _tela(raggio_angoli=0)
    ridotta = piena.resize((round(LATO * 0.62),) * 2, Image.LANCZOS)
    mascherabile = Image.new("RGBA", (LATO, LATO), (*ACQUA_SCURA, 255))
    posizione = (LATO - ridotta.width) // 2
    mascherabile.alpha_composite(ridotta, (posizione, posizione))
    mascherabile.resize((512, 512), Image.LANCZOS).save(CARTELLA / "icona-mascherabile.png")

    print(f"Icone scritte in {CARTELLA}")


if __name__ == "__main__":
    main()
