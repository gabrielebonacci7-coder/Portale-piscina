"""Ricava dall'icona disegnata le misure che vogliono telefono e manifest.

    python -m piscina.scripts.genera_icone

L'originale sta in `piscina/risorse/icona-originale.png`. Si rigenera solo
quando cambia il disegno: i file finiscono in `piscina/web/icone/`.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

RADICE = Path(__file__).resolve().parents[1]
ORIGINALE = RADICE / "risorse" / "icona-originale.png"
CARTELLA = RADICE / "web" / "icone"

# Quanto smusso hanno gli angoli delle icone di sistema, in proporzione al lato.
SMUSSO = 0.226
# Quanto spazio lasciare attorno all'icona mascherabile: Android la ritaglia
# come vuole (cerchio, goccia, quadrato stondato) e mangia i bordi.
RIENTRO = 0.66


def _ritaglia_al_disegno(img: Image.Image) -> Image.Image:
    """Toglie la cornice bianca attorno al quadrato dell'icona."""
    a = np.array(img).astype(int)
    # Non bianco: o è scuro, o tira all'azzurro più di quanto faccia il bianco.
    disegno = (a.sum(axis=2) < 720) | ((a[:, :, 2] - a[:, :, 0]) > 12)
    righe, colonne = np.where(disegno)
    quadrato = img.crop((colonne.min(), righe.min(), colonne.max() + 1, righe.max() + 1))
    lato = min(quadrato.size)
    return quadrato.resize((lato, lato), Image.LANCZOS)


def _riempi_gli_angoli(img: Image.Image) -> Image.Image:
    """Allunga il colore di bordo dentro gli angoli smussati del disegno.

    L'icona arriva già con gli angoli arrotondati, ma iOS e Android la smussano
    di nuovo per conto loro: senza questo passaggio restano quattro triangolini
    bianchi negli angoli.
    """
    p = np.array(img)
    for riga in p:
        pieni = np.where(riga.sum(axis=1) < 720)[0]
        if len(pieni) == 0:
            continue
        riga[: pieni[0]] = riga[pieni[0]]
        riga[pieni[-1] + 1 :] = riga[pieni[-1]]
    return Image.fromarray(p)


def main() -> None:
    CARTELLA.mkdir(parents=True, exist_ok=True)
    piena = _riempi_gli_angoli(_ritaglia_al_disegno(Image.open(ORIGINALE).convert("RGB")))
    lato = piena.width

    maschera = Image.new("L", (lato, lato), 0)
    ImageDraw.Draw(maschera).rounded_rectangle(
        [0, 0, lato - 1, lato - 1], radius=round(lato * SMUSSO), fill=255
    )
    smussata = piena.convert("RGBA")
    smussata.putalpha(maschera)
    for misura in (192, 512, 180):
        smussata.resize((misura, misura), Image.LANCZOS).save(CARTELLA / f"icona-{misura}.png")

    ridotta = piena.resize((round(lato * RIENTRO),) * 2, Image.LANCZOS)
    mascherabile = Image.new("RGB", (lato, lato), tuple(np.array(piena)[lato // 2, 4].tolist()))
    mascherabile.paste(ridotta, ((lato - ridotta.width) // 2,) * 2)
    mascherabile.resize((512, 512), Image.LANCZOS).save(CARTELLA / "icona-mascherabile.png")

    print(f"Icone scritte in {CARTELLA}")


if __name__ == "__main__":
    main()
