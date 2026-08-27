"""Scontorna l'illustrazione dell'omino e la prepara per l'app.

    python -m piscina.scripts.ritaglia_omino

Dall'originale con la raggiera arancione (`piscina/risorse/omino-originale.png`)
si ricava un WebP con lo sfondo trasparente, che l'app appoggia sopra
qualsiasi colore.

Lo sfondo si toglie in tre passaggi, perché uno solo non basta:

1. si riempie a partire dai bordi — il contorno scuro del disegno ferma il
   riempimento e sparisce tutto quello che sta attorno alla figura;
2. resta lo sfondo *chiuso dentro* il disegno (fra le gambe), dove il
   riempimento dai bordi non arriva: si parte da un punto scelto a mano;
3. l'ombra per terra è attaccata alle scarpe, quindi nessun riempimento la
   raggiunge: si toglie per colore, ma solo nella striscia in fondo.

Riconoscere lo sfondo dal solo colore non funziona: in questo disegno la pelle
è arancione quasi quanto la raggiera, e la faccia sparirebbe insieme a lei.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RADICE = Path(__file__).resolve().parents[1]
ORIGINALE = RADICE / "risorse" / "omino-originale.png"
DESTINAZIONE = RADICE / "web" / "immagini" / "omino.webp"

MAGENTA = (255, 0, 255)
# I due toni della raggiera, presi dall'originale.
TONI_SFONDO = ((252, 149, 15), (253, 192, 13))
# Il punto fra le gambe: sfondo circondato dal disegno.
SACCHE = ((436, 1189),)
# Larghezza finale: l'app lo mostra al massimo a 300 px, su schermi a densità
# doppia. Più grande di così sarebbero solo byte da scaricare.
LARGHEZZA = 600


def _e_sfondo(colore, tolleranza=30) -> bool:
    return any(
        sum(abs(c - t) for c, t in zip(colore, tono, strict=True)) < tolleranza
        for tono in TONI_SFONDO
    )


def main() -> None:
    img = Image.open(ORIGINALE).convert("RGB")
    larghezza, altezza = img.size
    lavoro = img.copy()

    semi = [(x, y) for x in range(0, larghezza, 10) for y in (0, altezza - 1)]
    semi += [(x, y) for y in range(0, altezza, 10) for x in (0, larghezza - 1)]
    for seme in semi:
        if lavoro.getpixel(seme) != MAGENTA:
            ImageDraw.floodfill(lavoro, seme, MAGENTA, thresh=72)

    for punto in SACCHE:
        colore = lavoro.getpixel(punto)
        if colore == MAGENTA:
            continue  # già preso dal riempimento dai bordi
        if not _e_sfondo(colore):
            raise SystemExit(f"il punto {punto} non è sfondo ma {colore}: disegno cambiato?")
        ImageDraw.floodfill(lavoro, punto, MAGENTA, thresh=72)

    a = np.array(lavoro)
    figura = ~((a[:, :, 0] == 255) & (a[:, :, 1] == 0) & (a[:, :, 2] == 255))

    r, b = a[:, :, 0].astype(int), a[:, :, 2].astype(int)
    ombra = (r > 170) & (b < 110) & ((r - b) > 90)
    ombra[: int(altezza * 0.90)] = False  # solo la striscia sotto le scarpe
    figura &= ~ombra

    alpha = Image.fromarray(np.where(figura, 255, 0).astype("uint8"), mode="L")
    # Un filo di erosione e sfocatura sul bordo: senza, resta l'alone arancione
    # del vecchio sfondo tutto attorno alla figura.
    # MinFilter(5) mangia due pixel di bordo: sotto, resta un filo arancione
    # tutto attorno alla figura, che sul fondo azzurro si vede benissimo. Il
    # disegno ha un contorno scuro spesso, quindi due pixel non gli fanno
    # niente.
    alpha = alpha.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(0.8))

    ritaglio = img.convert("RGBA")
    ritaglio.putalpha(alpha)
    ritaglio = ritaglio.crop(ritaglio.getbbox())

    finale = ritaglio.resize(
        (LARGHEZZA, round(LARGHEZZA * ritaglio.height / ritaglio.width)), Image.LANCZOS
    )
    DESTINAZIONE.parent.mkdir(parents=True, exist_ok=True)
    finale.save(DESTINAZIONE, quality=90, method=6)
    print(f"Omino scontornato in {DESTINAZIONE} ({finale.width}×{finale.height})")


if __name__ == "__main__":
    main()
