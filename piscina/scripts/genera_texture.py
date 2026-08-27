"""Disegna le texture della mappa: erba, acqua e pavimento del solarium.

    python -m piscina.scripts.genera_texture

Sono tre piastrelle da 256 pixel che si ripetono senza giunture, e la mappa le
usa come sfondo. Il perché di questo giro: la stessa grana fatta con i filtri
dell'SVG (feTurbulence) si ricalcola a ogni zoom, e su un telefono di tre anni
fa la mappa diventa una diapositiva. Una piastrella disegnata una volta sola si
ripete senza costare niente — tutte e tre insieme pesano una decina di
kilobyte.

Tutto è calcolato in modo **ciclico**: le distanze si misurano sul toro (chi
esce da destra rientra da sinistra) e le sfocature si fanno su una copia
affiancata nove volte. Senza queste due accortezze la ripetizione lascia il
reticolo, e la mappa sembra un pavimento di linoleum.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

CARTELLA = Path(__file__).resolve().parents[1] / "web" / "immagini"
LATO = 256


# --- attrezzi --------------------------------------------------------------
def _sfuma(a: np.ndarray, raggio: float) -> np.ndarray:
    """Sfoca un'immagine ciclica senza rompere la continuità ai bordi."""
    modo = "L" if a.ndim == 2 else "RGB"
    img = Image.fromarray(np.clip(a, 0, 255).astype("uint8"), mode=modo)
    grande = Image.new(modo, (LATO * 3, LATO * 3))
    for dx in range(3):
        for dy in range(3):
            grande.paste(img, (dx * LATO, dy * LATO))
    grande = grande.filter(ImageFilter.GaussianBlur(raggio))
    return np.array(grande.crop((LATO, LATO, LATO * 2, LATO * 2))).astype(float)


def _rumore(caso: np.random.Generator, raggio: float) -> np.ndarray:
    """Macchie morbide fra 0 e 1, senza giunture."""
    grezzo = caso.random((LATO, LATO)) * 255
    morbido = _sfuma(grezzo, raggio)
    minimo, massimo = morbido.min(), morbido.max()
    return (morbido - minimo) / max(massimo - minimo, 1e-6)


def _distanze_cicliche(punti: np.ndarray) -> np.ndarray:
    """Per ogni pixel, le distanze ai punti misurate sul toro.

    Restituisce un array (pixel, punti): serve a costruire il reticolo dei
    riflessi, che è fatto di *confini* fra celle, non di macchie.
    """
    y, x = np.mgrid[0:LATO, 0:LATO]
    coordinate = np.stack([x.ravel(), y.ravel()], axis=1).astype(float)
    dx = np.abs(coordinate[:, None, 0] - punti[None, :, 0])
    dy = np.abs(coordinate[:, None, 1] - punti[None, :, 1])
    # La distanza più corta può passare per il bordo opposto.
    dx = np.minimum(dx, LATO - dx)
    dy = np.minimum(dy, LATO - dy)
    return np.hypot(dx, dy)


# --- le tre grane ----------------------------------------------------------
def erba() -> Image.Image:
    """Un prato curato: verde uniforme, grana fine, le strisce del taglio.

    Le chiazze grosse fanno sembrare il prato malato; qui la variazione è
    piccola e la si sente più che vederla.
    """
    caso = np.random.default_rng(21)

    chiaro = np.array([138, 178, 96], dtype=float)
    scuro = np.array([104, 145, 74], dtype=float)

    # Variazione lenta: dove il prato è appena più fitto o più rado.
    fondo = _rumore(caso, 26)[..., None]
    tela = scuro + (chiaro - scuro) * (0.35 + 0.65 * fondo)

    # Le strisce del tosaerba: due passate, chiara e scura, appena accennate.
    x = np.arange(LATO)
    strisce = np.sin(x / LATO * np.pi * 4)[None, :, None]
    tela += strisce * 5.0

    # Grana dei fili: rumore fine, schiacciato in verticale come l'erba.
    fili = _sfuma(caso.random((LATO, LATO)) * 255, 0.45)
    fili = _sfuma(fili, 0.0)
    tela += ((fili - 128) / 128.0)[..., None] * 11.0

    return Image.fromarray(np.clip(tela, 0, 255).astype("uint8"), mode="RGB")


def acqua() -> Image.Image:
    """Acqua di piscina vista dall'alto: azzurro pulito e il reticolo del sole.

    I riflessi veri non sono ghirigori: sono una rete di linee chiare, i bordi
    delle celle in cui la superficie spezza la luce. Si ottengono misurando,
    per ogni punto, quanto sono vicini fra loro i due centri più prossimi: dove
    la differenza è quasi zero si è su un confine, e lì il fondo si illumina.
    """
    caso = np.random.default_rng(5)

    chiaro = np.array([86, 196, 232], dtype=float)
    scuro = np.array([28, 138, 190], dtype=float)

    profondita = _rumore(caso, 30)[..., None]
    tela = scuro + (chiaro - scuro) * (0.25 + 0.55 * profondita)

    def reticolo(quanti: int, larghezza: float, sfocatura: float) -> np.ndarray:
        punti = caso.random((quanti, 2)) * LATO
        vicine = np.sort(_distanze_cicliche(punti), axis=1)[:, :2]
        confine = (vicine[:, 1] - vicine[:, 0]).reshape(LATO, LATO)
        # Vicino a zero = sul confine fra due celle = riflesso.
        rete = np.clip(1.0 - confine / larghezza, 0, 1) ** 1.6
        return _sfuma(rete * 255, sfocatura) / 255.0

    # Due reti sovrapposte: una larga, che disegna il motivo, e una fitta e
    # tenue che le toglie la regolarità. Con una sola sembra un vetro rotto;
    # con due alla pari diventa latte.
    rete = np.clip(reticolo(30, 6.5, 1.7) + 0.22 * reticolo(85, 3.0, 1.0), 0, 1)

    luce = np.array([232, 251, 255], dtype=float)
    tela += (luce - tela) * (rete[..., None] * 0.5)

    return Image.fromarray(np.clip(tela, 0, 255).astype("uint8"), mode="RGB")


def pavimento() -> Image.Image:
    """Pietra chiara: granulosità fine e le fughe fra le mattonelle."""
    caso = np.random.default_rng(13)

    base = np.array([234, 222, 198], dtype=float)
    tela = np.repeat(np.repeat(base[None, None, :], LATO, 0), LATO, 1)

    macchie = _rumore(caso, 18)[..., None]
    tela += (macchie - 0.5) * 9.0
    grana = _sfuma(caso.random((LATO, LATO)) * 255, 0.5)
    tela += ((grana - 128) / 128.0)[..., None] * 7.0

    fuga = np.array([220, 205, 176], dtype=float)
    for i in (0, LATO // 2):
        tela[i : i + 2, :] = fuga
        tela[:, i : i + 2] = fuga

    return Image.fromarray(np.clip(tela, 0, 255).astype("uint8"), mode="RGB")


def main() -> None:
    CARTELLA.mkdir(parents=True, exist_ok=True)
    for nome, disegno in (("erba", erba()), ("acqua", acqua()), ("pavimento", pavimento())):
        percorso = CARTELLA / f"texture-{nome}.webp"
        disegno.save(percorso, quality=88, method=6)
        print(f"{percorso.name}: {percorso.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
