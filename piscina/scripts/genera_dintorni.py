"""Disegna la mappa dei dintorni della piscina.

    python -m piscina.scripts.genera_dintorni

Esce in `piscina/web/immagini/dintorni.svg`, quella che si vede nella pagina
"Dove siamo". È un disegno, non una mappa interattiva: serve a capire in due
secondi da che parte si entra e dove si lascia la macchina. Per le indicazioni
stradali vere ci sono i pulsanti che aprono Google Maps o Mappe.

Le posizioni vengono dalle foto satellitari, misurate con la barra di scala di
Google. Una scala sola per tutto, 2,5 pixel per metro: il campo da calcio è
100 x 64 m, la piscina col suo solarium 43 x 34 m — cioè il campo è tre volte
l'impianto della piscina, ed è così che si vede dall'alto. L'orientamento è
quello della foto: Via Superga scende da sinistra, l'impianto sta alla sua
destra, il cimitero più giù lungo la stessa strada.

Il cimitero è l'unica cosa non verificata: dalla foto sta a sud, ma non si
legge con certezza. Se è dall'altra parte, si cambia qui.

Il disegno si porta dentro il carattere, ridotto alle sole lettere che usa:
così si vede uguale dappertutto — dentro l'app, aperto da solo, mandato a
qualcuno — senza dipendere da quello che c'è installato sul telefono.
"""
import base64
import io
from pathlib import Path

W, H = 820, 470
K = 2.5                       # pixel per metro

CAMPI     = "#dfeac8"
CAMPI_2   = "#d4e3ba"
ULIVI     = "#bcd19d"
STRADA    = "#faf6ec"
STRADA_OR = "#ded2b9"
PIAZZALE  = "#e4dbcb"
ASFALTO   = "#d2c8b6"
COTTO     = "#b17a69"
COTTO_SC  = "#9a6453"
ACQUA     = "#19a8d0"
BIANCO    = "#f8f5ee"
ERBA      = "#6ca755"
ERBA_SC   = "#5d9549"
CIPRESSO  = "#4a7a52"
INK       = "#43352c"
INK_2     = "#6d5c51"
GIRO      = -10               # l'inclinazione dell'impianto
TS        = 1.0               # scala delle scritte (piu' grandi sul telefono)

def m(v): return v*K

def ombra(d, dx=3, dy=6, op=.16):
    return f'<g transform="translate({dx},{dy})" opacity="{op}">{d}</g>'

def testo(x, y, t, s=15, col=INK, peso=700, anc="middle", trk=.2, rot=None):
    r = f' transform="rotate({rot} {x} {y})"' if rot is not None else ''
    return (f'<text x="{x}" y="{y}" font-size="{s*TS:.1f}" font-weight="{peso}" fill="{col}" '
            f'text-anchor="{anc}" letter-spacing="{trk*TS:.2f}"{r}>{t}</text>')

def olivi():
    p = []
    for i in range(9):
        for j in range(4):
            x = 20 + j*40 + i*6
            y = 16 + i*54 - j*10
            if 0 < x < 170 and 0 < y < H-30:
                p.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{ULIVI}"/>')
    return "".join(p)

def posti_auto(x0, y0, n, dx, dy, ang):
    return "".join(
        f'<rect x="{x0+i*dx:.1f}" y="{y0+i*dy:.1f}" width="{m(5):.1f}" height="{m(2.3):.1f}" rx="1.6" '
        f'fill="{ASFALTO}" transform="rotate({ang} {x0+i*dx:.1f} {y0+i*dy:.1f})"/>' for i in range(n))

def griglia_auto(x, y, col, rig):
    return "".join(f'<rect x="{x+i*m(5.6):.1f}" y="{y+j*m(10):.1f}" width="{m(2.3):.1f}" '
                   f'height="{m(5):.1f}" rx="1.6" fill="{ASFALTO}"/>'
                   for i in range(col) for j in range(rig))

def chip(x, y, t="P", largo=26):
    w = largo*(1.0 if TS == 1.0 else 1.5)
    h = 26*(1.0 if TS == 1.0 else 1.45)
    return (f'<g>{ombra(f"""<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="{8*TS:.0f}" fill="{INK}"/>""",2,4,.2)}'
            f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="{8*TS:.0f}" fill="{BIANCO}"/>'
            f'{testo(x, y+6*TS, t, 16, INK_2, 800)}</g>')

def spillo(x, y, scala=1.0):
    return (f'<g transform="translate({x},{y}) scale({scala})">'
            f'<ellipse cx="2" cy="3" rx="12" ry="4.2" fill="{INK}" opacity=".25"/>'
            f'<path d="M0 0 C -12 -16 -18 -23 -18 -31 a 18 18 0 1 1 36 0 C 18 -23 12 -16 0 0 Z" fill="{ACQUA}"/>'
            f'<circle cy="-31" r="7" fill="{BIANCO}"/></g>')

def _carattere_dentro() -> str:
    """Il carattere del disegno, ridotto alle lettere che servono.

    Fuori da una pagina HTML un SVG non eredita i caratteri del sito: o se lo
    porta dentro, o scrive con quello di sistema."""
    from fontTools import subset
    from fontTools.ttLib import TTFont

    sorgente = Path(__file__).resolve().parents[1] / "web" / "font" / "inter.woff2"
    lettere = set("".join(ETICHETTE) + "0123456789 ,.·—")
    font = TTFont(sorgente)
    sottoinsieme = subset.Subsetter(subset.Options(layout_features=["kern", "liga"]))
    sottoinsieme.populate(text="".join(sorted(lettere)))
    sottoinsieme.subset(font)
    font.flavor = "woff2"
    memoria = io.BytesIO()
    font.save(memoria)
    dati = base64.b64encode(memoria.getvalue()).decode("ascii")
    return (
        "<style>@font-face{font-family:'Inter';font-weight:100 900;"
        f"src:url(data:font/woff2;base64,{dati}) format('woff2')}}</style>"
    )


# Tutte le scritte del disegno: servono a sapere quali lettere portarsi dentro.
ETICHETTE = [
    "Via Superga", "CIMITERO", "CAMPO SPORTIVO", "INGRESSO",
    "P interno", "P", "Piscina comunale", "50 m",
]


def mappa(compatta=False):
    global TS
    TS = 1.65 if compatta else 1.0
    d = [f'<rect width="{W}" height="{H}" fill="{CAMPI}"/>']
    d.append(f'<path d="M0 0 H250 L195 {H} H0 Z" fill="{CAMPI_2}"/>')
    d.append(f'<path d="M700 0 H{W} V170 L720 140 Z" fill="{CAMPI_2}"/>')
    d.append(olivi())

    # --- Via Superga ------------------------------------------------------
    via = "M 150 -30 L 236 180 L 292 320 L 372 500"
    d.append(f'<path d="{via}" stroke="{STRADA_OR}" stroke-width="42" fill="none" stroke-linecap="round" opacity=".45"/>')
    d.append(f'<path d="{via}" stroke="{STRADA}" stroke-width="36" fill="none" stroke-linecap="round"/>')
    d.append(f'<path d="{via}" stroke="{STRADA_OR}" stroke-width="1.6" fill="none" stroke-dasharray="10 12" opacity=".8"/>')
    d.append(testo(196, 112, "Via Superga", 15, INK_2, 700, "middle", .6, rot=68))

    # --- l'impianto, tutto inclinato insieme ------------------------------
    g = [f'<g transform="rotate({GIRO} 500 250)">']
    recinto = "M 300 48 L 676 28 L 706 392 L 330 420 Z"
    g.append(ombra(f'<path d="{recinto}" fill="{INK}"/>', 4, 8, .14))
    g.append(f'<path d="{recinto}" fill="{PIAZZALE}"/>')

    # piscina: solarium di cotto 43 x 34 m, con le due vasche vere
    px, py = 326, 64
    g.append(f'<rect x="{px-7}" y="{py-7}" width="{m(43)+14:.0f}" height="{m(34)+14:.0f}" rx="14" '
             f'fill="none" stroke="{ACQUA}" stroke-width="2.6" opacity=".38"/>')
    g.append(ombra(f'<rect x="{px}" y="{py}" width="{m(43):.0f}" height="{m(34):.0f}" rx="9" fill="{INK}"/>', 3, 6, .2))
    g.append(f'<rect x="{px}" y="{py}" width="{m(43):.0f}" height="{m(34):.0f}" rx="9" fill="{COTTO}"/>')
    g.append(f'<rect x="{px}" y="{py}" width="{m(43):.0f}" height="{m(34):.0f}" rx="9" fill="none" '
             f'stroke="{COTTO_SC}" stroke-width="1.8"/>')
    # vasca grande 25 x 12,7 e vasca bambini 8 x 4
    vx, vy = px+m(9), py+m(7)
    g.append(f'<rect x="{vx:.0f}" y="{vy:.0f}" width="{m(25):.0f}" height="{m(12.7):.0f}" rx="4" fill="{BIANCO}"/>')
    g.append(f'<rect x="{vx+3:.0f}" y="{vy+3:.0f}" width="{m(25)-6:.0f}" height="{m(12.7)-6:.0f}" rx="2.5" fill="{ACQUA}"/>')
    g.append(f'<rect x="{px+m(26):.0f}" y="{py+m(24):.0f}" width="{m(8):.0f}" height="{m(4):.0f}" rx="2.5" fill="{BIANCO}"/>')
    g.append(f'<rect x="{px+m(26)+2:.0f}" y="{py+m(24)+2:.0f}" width="{m(8)-4:.0f}" height="{m(4)-4:.0f}" rx="1.5" fill="{ACQUA}"/>')
    # spogliatoi e bar, il filo di fabbricati a sud
    g.append(f'<rect x="{px+m(4):.0f}" y="{py+m(29):.0f}" width="{m(22):.0f}" height="{m(4.5):.0f}" rx="2" fill="{COTTO_SC}"/>')

    # campo sportivo 100 x 64 m
    cx, cy = 326, 196
    cw, ch = m(100), m(64)
    g.append(ombra(f'<rect x="{cx}" y="{cy}" width="{cw:.0f}" height="{ch:.0f}" rx="6" fill="{INK}"/>', 3, 6, .16))
    g.append(f'<rect x="{cx}" y="{cy}" width="{cw:.0f}" height="{ch:.0f}" rx="6" fill="{ERBA}"/>')
    g.append("".join(f'<rect x="{cx+i*cw/8:.0f}" y="{cy}" width="{cw/16:.0f}" height="{ch:.0f}" '
                     f'fill="{ERBA_SC}" opacity=".32"/>' for i in range(8)))
    mx, my, mw, mh = cx+8, cy+8, cw-16, ch-16
    g.append(f'<rect x="{mx}" y="{my}" width="{mw:.0f}" height="{mh:.0f}" fill="none" stroke="{BIANCO}" stroke-width="1.8"/>'
             f'<line x1="{mx+mw/2:.0f}" y1="{my}" x2="{mx+mw/2:.0f}" y2="{my+mh:.0f}" stroke="{BIANCO}" stroke-width="1.8"/>'
             f'<circle cx="{mx+mw/2:.0f}" cy="{my+mh/2:.0f}" r="{m(9.15):.0f}" fill="none" stroke="{BIANCO}" stroke-width="1.8"/>'
             f'<rect x="{mx}" y="{my+mh/2-m(20):.0f}" width="{m(16):.0f}" height="{m(40):.0f}" fill="none" stroke="{BIANCO}" stroke-width="1.8"/>'
             f'<rect x="{mx+mw-m(16):.0f}" y="{my+mh/2-m(20):.0f}" width="{m(16):.0f}" height="{m(40):.0f}" fill="none" stroke="{BIANCO}" stroke-width="1.8"/>')

    # parcheggio grande, a est del campo
    g.append(f'<rect x="{cx+cw+10:.0f}" y="{cy+6:.0f}" width="{m(26):.0f}" height="{m(58):.0f}" rx="6" fill="{PIAZZALE}"/>')
    g.append(griglia_auto(cx+cw+20, cy+18, 3, 5))
    # piazzale d'ingresso fra strada e piscina
    g.append(griglia_auto(312, 84, 1, 4))
    g.append('</g>')
    d.append("".join(g))

    # --- posti auto lungo la strada ---------------------------------------
    d.append(posti_auto(258, 196, 11, 5.4, 14.0, 24))
    d.append(chip(282, 292))

    # --- il cimitero, piu' a sud lungo la strada --------------------------
    c = [f'<g transform="rotate({GIRO} 540 440)">']
    c.append(f'<path d="M 330 430 L 770 392 L 800 {H+40} L 352 {H+40} Z" fill="{PIAZZALE}"/>')
    c.append(f'<rect x="372" y="424" width="200" height="28" rx="4" fill="{BIANCO}" opacity=".85"/>')
    c.append("".join(f'<ellipse cx="{600+i*27}" cy="{420-i*2}" rx="6.5" ry="11" fill="{CIPRESSO}"/>' for i in range(6)))
    c.append('</g>')
    d.append("".join(c))
    d.append(testo(404, 434, "CIMITERO", 12.5 if not compatta else 9, INK_2, 800, "middle", 1.8, rot=GIRO))
    d.append(chip(634, 414))

    # --- etichette --------------------------------------------------------
    d.append(testo(470, 348, "CAMPO SPORTIVO", 13 if not compatta else 8.6, BIANCO, 800, "middle", 2.4, rot=GIRO))
    # l'ingresso della piscina, dove si entra dalla strada
    d.append(spillo(306, 222, 0.95 if not compatta else 1.4))
    lw, lh = (188, 34) if not compatta else (300, 52)
    lx, ly = (374, 22) if not compatta else (330, 12)
    d.append(f'<g>{ombra(f"""<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="11" fill="{INK}"/>""",2,5,.22)}'
             f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="{11 if not compatta else 15}" fill="{BIANCO}"/>'
             f'{testo(lx+lw/2, ly+lh*0.68, "Piscina comunale", 15.5, INK, 700, "middle", .1)}</g>')
    iw, ih = (104, 25) if not compatta else (168, 38)
    ix, iy = (150, 196) if not compatta else (116, 190)
    d.append(f'<g>{ombra(f"""<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="8" fill="{INK}"/>""",2,4,.18)}'
             f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="{8 if not compatta else 12}" fill="{ACQUA}"/>'
             f'{testo(ix+iw/2, iy+ih*0.68, "INGRESSO", 11, BIANCO, 800, "middle", 1.4)}</g>')
    d.append(chip(652 if not compatta else 668, 236, "P interno", 86))

    # barra di scala: 50 m (solo nella versione grande)
    sb = m(50)
    if compatta:
        return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
                f'font-family="Inter, system-ui, sans-serif">{_carattere_dentro()}{"".join(d)}</svg>')
    d.append(f'<g><line x1="34" y1="{H-30}" x2="{34+sb:.0f}" y2="{H-30}" stroke="{INK_2}" stroke-width="2.4"/>'
             f'<line x1="34" y1="{H-36}" x2="34" y2="{H-24}" stroke="{INK_2}" stroke-width="2.4"/>'
             f'<line x1="{34+sb:.0f}" y1="{H-36}" x2="{34+sb:.0f}" y2="{H-24}" stroke="{INK_2}" stroke-width="2.4"/>'
             f'{testo(34+sb/2, H-42, "50 m", 13, INK_2, 700)}</g>')

    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Inter, system-ui, sans-serif">{_carattere_dentro()}{"".join(d)}</svg>')


def main() -> None:
    uscita = Path(__file__).resolve().parents[1] / "web" / "immagini" / "dintorni.svg"
    uscita.write_text(mappa(compatta=True), encoding="utf-8")
    print(f"Mappa dei dintorni: {uscita} ({uscita.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
