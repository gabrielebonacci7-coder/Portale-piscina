"""Genera le foto di esempio per il seed.

Non sono fotografie: sono immagini disegnate, così il repository non porta
con sé file binari pesanti né foto di persone vere.
"""

from io import BytesIO

from PIL import Image, ImageDraw

# Stessi colori dell'interfaccia.
ACQUA = (11, 110, 127)
ACQUA_CHIARA = (69, 180, 196)
SABBIA = (237, 242, 241)
PIETRA = (150, 165, 168)
ROSSO = (196, 56, 31)


def _tela(larghezza=1200, altezza=800, sfondo=SABBIA) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (larghezza, altezza), sfondo)
    return img, ImageDraw.Draw(img)


def _bytes(img: Image.Image) -> bytes:
    buffer = BytesIO()
    img.save(buffer, "JPEG", quality=88)
    return buffer.getvalue()


def ritratto(iniziale: str, tinta=ACQUA) -> bytes:
    """Un ritratto stilizzato: cerchio della testa e spalle su fondo tinto."""
    img, d = _tela(600, 600, tinta)
    d.ellipse([210, 130, 390, 310], fill=SABBIA)
    d.ellipse([140, 350, 460, 720], fill=SABBIA)
    return _bytes(img)


def ingresso(nome: str) -> bytes:
    """Facciata con cancello e insegna: è la foto che fa trovare il posto."""
    img, d = _tela()
    d.rectangle([0, 0, 1200, 300], fill=(196, 222, 226))  # cielo
    d.rectangle([0, 620, 1200, 800], fill=PIETRA)  # marciapiede
    d.rectangle([120, 180, 1080, 640], fill=SABBIA, outline=PIETRA, width=6)
    d.rectangle([430, 330, 770, 640], fill=ACQUA)  # portone
    for x in range(450, 770, 40):  # sbarre del cancello
        d.line([x, 330, x, 640], fill=ACQUA_CHIARA, width=6)
    d.rectangle([380, 220, 820, 300], fill=ACQUA)  # insegna
    d.text((470, 250), nome[:16], fill=SABBIA)
    return _bytes(img)


def vasca() -> bytes:
    """Vasca vista dall'alto, con le corsie."""
    img, d = _tela()
    d.rectangle([0, 0, 1200, 800], fill=PIETRA)
    d.rectangle([90, 120, 1110, 680], fill=ACQUA)
    for y in range(200, 680, 95):  # galleggianti delle corsie
        for x in range(110, 1100, 46):
            d.ellipse([x, y, x + 30, y + 30], fill=ACQUA_CHIARA)
    return _bytes(img)


def spogliatoi() -> bytes:
    """Fila di armadietti."""
    img, d = _tela()
    d.rectangle([0, 0, 1200, 800], fill=(214, 226, 226))
    for i, x in enumerate(range(80, 1120, 180)):
        d.rectangle([x, 140, x + 150, 700], fill=ACQUA if i % 2 else ACQUA_CHIARA, outline=SABBIA, width=4)
        d.ellipse([x + 118, 400, x + 134, 416], fill=SABBIA)  # maniglia
    return _bytes(img)


def salvagente() -> bytes:
    """Salvagente appeso: foto generica di attrezzatura."""
    img, d = _tela()
    d.rectangle([0, 0, 1200, 800], fill=(226, 236, 236))
    d.ellipse([390, 190, 810, 610], outline=ROSSO, width=90)
    d.line([600, 150, 600, 240], fill=PIETRA, width=14)
    return _bytes(img)
