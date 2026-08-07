"""Genera le icone PNG della PWA a partire dallo stesso disegno dell'SVG.

    python -m scripts.genera_icone

Il segno è una boa di salvataggio: anello in laguna, quattro fasce in rosso
salvagente. Si rigenerano solo quando cambia il marchio.
"""

from pathlib import Path

from PIL import Image, ImageDraw

DESTINAZIONE = Path(__file__).resolve().parents[1] / "web" / "icone"

ACCENTO = (11, 110, 127)
ROSSO = (196, 56, 31)
FONDO = (237, 242, 241)

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#edf2f1"/>
  <circle cx="32" cy="32" r="20" fill="none" stroke="#0b6e7f" stroke-width="7"/>
  <path d="M32 10v12M32 42v12M10 32h12M42 32h12"
        stroke="#c4381f" stroke-width="7" stroke-linecap="round"/>
</svg>
"""


def disegna(lato: int, margine: float = 0.0) -> Image.Image:
    """Disegna l'icona. `margine` rimpicciolisce il segno per le icone
    mascherabili di Android, che vengono ritagliate ai bordi."""
    # Si disegna 4 volte più grande e si rimpicciolisce: è il modo più
    # semplice per avere i bordi morbidi senza antialiasing manuale.
    s = lato * 4
    img = Image.new("RGBA", (s, s), FONDO + (255,))
    d = ImageDraw.Draw(img)

    centro = s / 2
    raggio = s * (0.315 - margine)
    spessore = int(s * 0.11)

    d.ellipse(
        [centro - raggio, centro - raggio, centro + raggio, centro + raggio],
        outline=ACCENTO,
        width=spessore,
    )

    interno = raggio - spessore * 0.9
    esterno = raggio + spessore * 0.9
    meta = spessore / 2
    for x0, y0, x1, y1 in [
        (centro, centro - esterno, centro, centro - interno),  # alto
        (centro, centro + interno, centro, centro + esterno),  # basso
        (centro - esterno, centro, centro - interno, centro),  # sinistra
        (centro + interno, centro, centro + esterno, centro),  # destra
    ]:
        d.line([x0, y0, x1, y1], fill=ROSSO, width=spessore)
        # Estremi arrotondati, che PIL non fa da solo sulle linee.
        for cx, cy in ((x0, y0), (x1, y1)):
            d.ellipse([cx - meta, cy - meta, cx + meta, cy + meta], fill=ROSSO)

    return img.resize((lato, lato), Image.LANCZOS)


def main() -> None:
    DESTINAZIONE.mkdir(parents=True, exist_ok=True)
    (DESTINAZIONE / "icona.svg").write_text(SVG, encoding="utf-8")

    for lato, nome in [(192, "icona-192.png"), (512, "icona-512.png"), (180, "icona-180.png")]:
        disegna(lato).save(DESTINAZIONE / nome)

    # Android ritaglia le icone mascherabili in un cerchio: il segno va
    # tenuto dentro la "zona sicura", circa l'80% del lato.
    disegna(512, margine=0.06).save(DESTINAZIONE / "icona-mascherabile.png")

    print(f"Icone generate in {DESTINAZIONE}")
    for f in sorted(DESTINAZIONE.iterdir()):
        print(f"  {f.name}  {f.stat().st_size / 1024:.1f} kB")


if __name__ == "__main__":
    main()
