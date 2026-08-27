"""La piantina del solarium: dove sta ogni cosa, in coordinate.

È l'unica fonte della verità della vista dall'alto: il backend la serve e la
PWA disegna esattamente quello che trova qui. Se un giorno la disposizione
cambia (una fila in più, il gazebo spostato), si tocca solo questo file — non
il disegno, non il database, non l'app.

Le coordinate sono in unità della viewBox SVG, non in pixel né in metri:
l'origine è in alto a sinistra, la x cresce verso destra, la y verso il basso.
La mappa è orientata come lo schizzo fatto a mano: l'ingresso e la cassa in
basso a sinistra, il campo da beach volley in alto, le due vasche al centro.

Le 50 postazioni sono numerate per fila, dalla lettera che sta più vicino
all'ingresso della vasca grande:

    A  (12)  la fila lunga sopra la vasca grande
    B  (12)  la fila sul lato destro, verso le docce
    C   (8)  sotto la vasca grande, accanto alla postazione del bagnino
    D   (8)  fra la vasca piccola e il prato
    E  (10)  la fila in fondo, davanti all'ingresso
    S  (12)  i lettini singoli delle due zone solarium (senza ombrellone)

Il codice è quello che si dice ad alta voce in cassa ("C7"): deve essere
uguale a quello scritto sulla postazione, altrimenti l'app e il bagnino
parlano due lingue diverse.
"""

VIEWBOX = "0 0 1020 1040"

# Le file che stanno di traverso: la B corre lungo il lato destro, e i suoi
# lettini vanno girati di un quarto per guardare la vasca invece dell'ingresso.
ROTAZIONI = {"B": 90}

# Quanti lettini stanno sotto un ombrellone. Il listino arriva a "Postazione
# Relax 3" = 1 ombrellone + 3 lettini, e più di così non ci si sta.
MAX_LETTINI_OMBRELLONE = 3

# Quanti lettini mostra la mappa sotto un ombrellone libero: due, perché è
# come sono messi di solito. Chi ne vuole uno solo, o tre, lo sceglie dopo.
LETTINI_DISEGNATI = 2


def _fila(lettera: str, quanti: int, x0: float, y0: float, passo_x: float, passo_y: float):
    """Una fila di ombrelloni equidistanti, numerati da 1."""
    return [
        {
            "codice": f"{lettera}{i + 1}",
            "tipo": "ombrellone",
            "fila": lettera,
            "x": x0 + i * passo_x,
            "y": y0 + i * passo_y,
            "max_lettini": MAX_LETTINI_OMBRELLONE,
        }
        for i in range(quanti)
    ]


def _lettini(numeri: range, coordinate: list[tuple[float, float]]):
    """I lettini singoli del solarium: niente ombrellone sopra."""
    return [
        {
            "codice": f"S{n}",
            "tipo": "lettino",
            "fila": "S",
            "x": x,
            "y": y,
            "max_lettini": 0,
        }
        for n, (x, y) in zip(numeri, coordinate, strict=True)
    ]


# --- Le postazioni ---------------------------------------------------------
POSTAZIONI: list[dict] = [
    *_fila("A", 12, x0=336, y0=196, passo_x=42, passo_y=0),
    *_fila("B", 12, x0=884, y0=206, passo_x=0, passo_y=44),
    *_fila("C", 8, x0=336, y0=622, passo_x=60, passo_y=0),
    *_fila("D", 8, x0=296, y0=764, passo_x=44, passo_y=0),
    *_fila("E", 10, x0=300, y0=902, passo_x=60, passo_y=0),
    # Solarium in alto a sinistra: sei lettini su due colonne.
    *_lettini(
        range(1, 7),
        [(112, 220), (200, 220), (112, 252), (200, 252), (112, 284), (200, 284)],
    ),
    # Solarium sotto, stessa disposizione.
    *_lettini(
        range(7, 13),
        [(112, 396), (200, 396), (112, 428), (200, 428), (112, 460), (200, 460)],
    ),
]

# --- Tutto il resto: le cose che non si prenotano ma servono a orientarsi ---
# Senza la vasca e la cassa, cinquanta pallini sono cinquanta pallini: uno
# guarda lo schermo e non sa da che parte è girato.
SCENOGRAFIA: list[dict] = [
    {"tipo": "recinto", "x": 40, "y": 158, "w": 940, "h": 852},
    {"tipo": "volley", "etichetta": "Campo beach volley", "x": 404, "y": 26, "w": 326, "h": 116},
    {"tipo": "solarium", "etichetta": "Solarium", "x": 58, "y": 176, "w": 196, "h": 128},
    {"tipo": "solarium", "etichetta": "Solarium", "x": 58, "y": 352, "w": 196, "h": 128},
    {"tipo": "vasca", "etichetta": "Piscina", "x": 320, "y": 244, "w": 480, "h": 268},
    {"tipo": "vasca", "etichetta": "Piscina piccola", "x": 626, "y": 700, "w": 240, "h": 166},
    {"tipo": "bagnino", "etichetta": "Bagnino", "x": 536, "y": 540, "w": 48, "h": 52},
    {"tipo": "doccia", "etichetta": "Docce", "x": 892, "y": 720, "w": 80, "h": 84},
    {"tipo": "cassa", "etichetta": "Cassa e ingresso", "x": 58, "y": 856, "w": 196, "h": 136},
    # Le palme sono decorazione, non catasto: servono a far sembrare una
    # piscina quello che altrimenti è una griglia di pallini. Stanno negli
    # angoli di pavimento dove non passa nessuno, e si tolgono da qui senza
    # toccare nient'altro.
    {"tipo": "palma", "x": 96, "y": 536, "w": 58, "h": 58},
    {"tipo": "palma", "x": 186, "y": 632, "w": 46, "h": 46},
    {"tipo": "palma", "x": 84, "y": 736, "w": 50, "h": 50},
    {"tipo": "palma", "x": 902, "y": 872, "w": 54, "h": 54},
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
