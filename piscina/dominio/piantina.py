"""La piantina del solarium: dove sta ogni cosa, in coordinate.

È l'unica fonte della verità della vista dall'alto: il backend la serve e la
PWA disegna esattamente quello che trova qui. Se un giorno la disposizione
cambia (una fila in più, un ombrellone spostato), si tocca solo questo file —
non il disegno, non il database, non l'app.

**Le misure sono quelle vere.** Vengono dall'elaborato grafico del geometra
(planimetria in scala 1:200) e sono state ricontrollate sulle foto satellitari:

    vasca adulti      25,00 x 12,70 m
    vasca bambini      8,10 x  4,10 m, appoggiata all'angolo sud-est
    solarium          un poligono di circa 43 x 34 m tutto intorno

Qui si lavora in **metri**, con l'origine nell'angolo nord-ovest della vasca
grande: `x` cresce verso l'altro capo della vasca, `y` verso gli spogliatoi.
Le funzioni `X()` e `Y()` traducono in unità della viewBox SVG — venti per
metro — e solo quelle finiscono nel disegno.

Nel progetto l'impianto è ruotato di 29°: qui la pianta è raddrizzata, perché
su un telefono tenuto dritto si legge molto meglio.

Le 38 postazioni sono numerate per fila:

    A (10)  la fila lunga a nord, fra gli alberi e la vasca
    B  (6)  la colonna a est, in fondo alla vasca
    C  (7)  la prima fila a sud della vasca
    D  (4)  la fila di mezzo, verso l'ingresso
    E  (3)  la fila bassa a sud-ovest, dove il cotto finisce prima
    F  (5)  sotto la vasca dei bambini
    G  (3)  la colonna a ovest, davanti alle docce
    S  (8)  i lettini singoli in riva alla vasca, senza ombrellone

Il codice è quello che si dice ad alta voce in cassa ("C7"): deve essere
uguale a quello scritto sulla postazione, altrimenti l'app e il bagnino
parlano due lingue diverse.
"""

M = 20                      # unità di disegno per metro
A_MIN, B_MIN = -19.0, -15.0  # angolo in alto a sinistra della finestra
LARGHEZZA, ALTEZZA = 54.0, 50.0

VIEWBOX = f"0 0 {int(LARGHEZZA * M)} {int(ALTEZZA * M)}"


def X(a: float) -> float:
    """Metri da ovest → unità di disegno."""
    return round((a - A_MIN) * M, 1)


def Y(b: float) -> float:
    """Metri da nord → unità di disegno."""
    return round((b - B_MIN) * M, 1)


def _q(a: float, b: float, la: float, lb: float) -> dict:
    """Un rettangolo dato in metri, tradotto in unità di disegno."""
    return {"x": X(a), "y": Y(b), "w": round(la * M, 1), "h": round(lb * M, 1)}


def _linea(punti: list[tuple[float, float]]) -> list[list[float]]:
    return [[X(a), Y(b)] for a, b in punti]


# Nessuna fila va girata: dall'alto un ombrellone è un cerchio, e un cerchio
# ruotato resta lo stesso cerchio. La chiave resta per i lettini del solarium.
ROTAZIONI: dict[str, int] = {}

MAX_LETTINI_OMBRELLONE = 3

# Quanti lettini mostra la scheda di un ombrellone libero: due, perché è come
# sono messi di solito. Chi ne vuole uno solo, o tre, lo sceglie dopo.
LETTINI_DISEGNATI = 2

# --- Dove stanno gli ombrelloni, in metri ----------------------------------
# Passo 3,90 m: a occhio sembra tanto, ma un parasole aperto misura due metri
# e mezzo e due ombrelloni attaccati non li vuole nessuno. Nessuna postazione
# esce dal pavimento: a sud-ovest il cotto si ferma prima, e le file corte
# della E e della G sono corte per quello.
_FILE: list[tuple[str, list[tuple[float, float]]]] = [
    ("A", [(-8.6 + 3.9 * i, -4.2) for i in range(10)]),
    ("B", [(27.3, 0.6 + 3.9 * i) for i in range(6)]),
    ("C", [(-2.2 + 3.9 * i, 15.6) for i in range(7)]),
    ("D", [(-2.2 + 3.9 * i, 19.8) for i in range(4)]),
    ("E", [(-2.2 + 3.9 * i, 22.4) for i in range(3)]),
    ("F", [(12.5 + 3.9 * i, 24.6) for i in range(5)]),
    ("G", [(-8.6, 5.5 + 3.9 * i) for i in range(3)]),
]

# I lettini singoli: la fila in riva alla vasca, come nelle foto della piscina.
# Non hanno ombrellone sopra e si pagano a parte.
_LETTINI_RIVA = [(1.8 + 3.1 * i, -1.5) for i in range(8)]


def _fila(lettera: str, punti: list[tuple[float, float]]) -> list[dict]:
    return [
        {
            "codice": f"{lettera}{i + 1}",
            "tipo": "ombrellone",
            "fila": lettera,
            "x": X(a),
            "y": Y(b),
            "max_lettini": MAX_LETTINI_OMBRELLONE,
        }
        for i, (a, b) in enumerate(punti)
    ]


POSTAZIONI: list[dict] = [
    *[p for lettera, punti in _FILE for p in _fila(lettera, punti)],
    *[
        {
            "codice": f"S{i + 1}",
            "tipo": "lettino",
            "fila": "S",
            "x": X(a),
            "y": Y(b),
            "max_lettini": 0,
        }
        for i, (a, b) in enumerate(_LETTINI_RIVA)
    ],
]

# --- Tutto il resto: le cose che non si prenotano ma servono a orientarsi ---
# Senza le vasche, gli spogliatoi e la fila di alberi, trentotto pallini sono
# trentotto pallini: uno guarda lo schermo e non sa da che parte è girato.
_ALBERI_FILA = [(-8.0 + 2.55 * i, -9.6) for i in range(12)]
_ALBERI_SPARSI = [
    (-16.0, -10.2), (-13.2, -6.0), (-14.8, 0.4), (-12.0, -12.4), (-6.4, -11.6),
    (-1.0, -12.9), (3.4, -11.4), (9.0, -12.8), (14.2, -11.5), (19.8, -12.9),
    (25.2, -11.7), (30.0, -12.2), (31.6, -6.2), (31.4, 2.6), (31.8, 11.4),
    (31.4, 20.2), (31.6, 28.4), (-15.6, 8.8),
]

SCENOGRAFIA: list[dict] = [
    # La siepe che chiude il recinto, vista dall'alto: una fascia verde scuro.
    {
        "tipo": "siepe",
        "punti": _linea([(-17.6, 32.6), (-17.6, -13.4), (31.2, -13.4),
                         (33.4, -9.4), (33.4, 32.6)]),
        "spessore": round(1.6 * M, 1),
    },
    # Il pavimento di cotto: il poligono vero, con il taglio verso la cassa.
    {
        "tipo": "pavimento",
        "punti": _linea([(-11, -7.5), (29.5, -7.5), (29.5, 26.5), (11, 26.5),
                         (9, 23.5), (-4, 23.5), (-13.5, 17), (-13.5, 10.5), (-11, 7)]),
    },
    {"tipo": "vasca", "etichetta": "Piscina", "corsie": 6, **_q(0, 0, 25, 12.7)},
    {"tipo": "vasca", "etichetta": "Vasca bambini", **_q(16.8, 17.2, 8.1, 4.1)},
    {"tipo": "edificio", "etichetta": "Spogliatoi", "tetto": True, **_q(-4.0, 26.6, 20.0, 4.6)},
    {"tipo": "edificio", "etichetta": "Bar", "tetto": True, **_q(17.0, 26.6, 12.5, 4.6)},
    {"tipo": "edificio", "etichetta": "Cassa", "tetto": True, **_q(-13.4, 24.0, 8.2, 4.4)},
    {"tipo": "edificio", "etichetta": "Docce", **_q(-12.8, -3.0, 4.2, 3.4)},
    {"tipo": "edificio", **_q(-12.8, 1.2, 4.2, 3.0)},
    {"tipo": "bagnino", "etichetta": "Bagnino", "x": X(-2.3), "y": Y(6.4), "r": round(0.95 * M, 1)},
    *[
        {"tipo": "albero", "x": X(a), "y": Y(b), "r": round(r * M, 1)}
        for a, b, r in [(*p, 1.05) for p in _ALBERI_FILA] + [(*p, 1.5) for p in _ALBERI_SPARSI]
    ],
]


def rotazione(fila: str) -> int:
    return ROTAZIONI.get(fila, 0)


def conta() -> dict[str, int]:
    """Quante postazioni di ogni tipo: serve ai test e alla pagina prezzi."""
    ombrelloni = sum(1 for p in POSTAZIONI if p["tipo"] == "ombrellone")
    return {
        "ombrelloni": ombrelloni,
        "lettini_solarium": len(POSTAZIONI) - ombrelloni,
        "totale": len(POSTAZIONI),
    }
