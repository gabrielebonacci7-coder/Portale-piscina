"""Genera le icone PNG e l'SVG del marchio Guardlink.

    python -m scripts.genera_icone

Il segno è un salvagente: anello rosso con quattro settori bianchi, come
quelli veri appesi a bordo vasca. Sta su un fondo scuro perché il bianco
abbia contrasto — e perché sulla schermata home di un telefono un'icona
scura si distingue fra tante chiare.

Si rigenerano solo quando cambia il marchio.
"""

from pathlib import Path

from PIL import Image, ImageDraw

DESTINAZIONE = Path(__file__).resolve().parents[1] / "web" / "icone"

# Rosso salvagente, un filo più caldo del rosso "urgenza" dell'interfaccia.
ROSSO = (214, 62, 38)
BIANCO = (255, 255, 255)
FONDO = (12, 42, 46)  # lo stesso inchiostro scuro dell'app

# I settori bianchi stanno sulle diagonali: è la disposizione classica.
SETTORI_BIANCHI = [(22.5, 67.5), (112.5, 157.5), (202.5, 247.5), (292.5, 337.5)]

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img"
     aria-label="Guardlink">
  <rect width="64" height="64" rx="14" fill="#0c2a2e"/>
  <circle cx="32" cy="32" r="19" fill="none" stroke="#ffffff" stroke-width="10"/>
  <!-- L'anello rosso a tratti scopre il bianco sottostante: quattro settori
       per parte, sfalsati di mezzo passo perché il bianco cada sulle diagonali. -->
  <circle cx="32" cy="32" r="19" fill="none" stroke="#d63e26" stroke-width="10"
          stroke-dasharray="14.92 14.92" stroke-dashoffset="7.46"/>
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
    raggio = s * (0.297 - margine)
    spessore = int(s * 0.156)
    riquadro = [centro - raggio, centro - raggio, centro + raggio, centro + raggio]

    # Prima l'anello rosso pieno, poi i settori bianchi sopra.
    d.ellipse(riquadro, outline=ROSSO, width=spessore)
    for inizio, fine in SETTORI_BIANCHI:
        d.arc(riquadro, inizio, fine, fill=BIANCO, width=spessore)

    return img.resize((lato, lato), Image.LANCZOS)


def main() -> None:
    DESTINAZIONE.mkdir(parents=True, exist_ok=True)
    (DESTINAZIONE / "icona.svg").write_text(SVG, encoding="utf-8")

    for lato, nome in [(192, "icona-192.png"), (512, "icona-512.png"), (180, "icona-180.png")]:
        disegna(lato).save(DESTINAZIONE / nome)

    # Android ritaglia le icone mascherabili in un cerchio: il segno va
    # tenuto dentro la "zona sicura", circa l'80% del lato.
    disegna(512, margine=0.055).save(DESTINAZIONE / "icona-mascherabile.png")

    print(f"Icone generate in {DESTINAZIONE}")
    for f in sorted(DESTINAZIONE.iterdir()):
        print(f"  {f.name}  {f.stat().st_size / 1024:.1f} kB")


if __name__ == "__main__":
    main()
