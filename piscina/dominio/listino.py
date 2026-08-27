"""Il listino 2026, copiato dal cartello affisso in piscina.

Tutti gli importi sono in **centesimi**: sui soldi non si usano i decimali in
virgola mobile, perché 0.1 + 0.2 non fa 0.3 e a fine stagione i conti non
tornano. Si formattano in euro solo quando si mostrano.

Gli sconti per gli abbonati non si calcolano: sono scritti sul cartello già
arrotondati (7 € meno il 20% farebbe 5,60 e il cartello dice 5), e il prezzo
che paga il cliente deve essere quello esposto, non quello che viene fuori da
una moltiplicazione.
"""

TARIFFA_INTERA = "intera"
TARIFFA_SETTIMANALE = "abbonato_settimanale"
TARIFFA_MENSILE = "abbonato_mensile"

# Noleggio attrezzature, al giorno. La chiave è il numero di lettini presi
# insieme all'ombrellone: 0 = solo ombrellone, 1..3 = "Postazione Relax 1..3".
OMBRELLONE: dict[int, dict[str, int]] = {
    0: {TARIFFA_INTERA: 500, TARIFFA_SETTIMANALE: 400, TARIFFA_MENSILE: 300},
    1: {TARIFFA_INTERA: 700, TARIFFA_SETTIMANALE: 500, TARIFFA_MENSILE: 400},
    2: {TARIFFA_INTERA: 1200, TARIFFA_SETTIMANALE: 900, TARIFFA_MENSILE: 800},
    3: {TARIFFA_INTERA: 1700, TARIFFA_SETTIMANALE: 1300, TARIFFA_MENSILE: 1100},
}

# Lettino singolo, quello del solarium: niente ombrellone sopra.
LETTINO: dict[str, int] = {
    TARIFFA_INTERA: 500,
    TARIFFA_SETTIMANALE: 400,
    TARIFFA_MENSILE: 300,
}

NOMI_PACCHETTO = {
    0: "Ombrellone",
    1: "Postazione Relax 1 (ombrellone + 1 lettino)",
    2: "Postazione Relax 2 (ombrellone + 2 lettini)",
    3: "Postazione Relax 3 (ombrellone + 3 lettini)",
}


def prezzo_cent(tipo: str, lettini: int, tariffa: str = TARIFFA_INTERA) -> int:
    """Quanto costa una postazione per una giornata di noleggio."""
    if tipo == "lettino":
        return LETTINO[tariffa]
    if lettini not in OMBRELLONE:
        raise ValueError(f"lettini fuori dal listino: {lettini}")
    return OMBRELLONE[lettini][tariffa]


def euro(cent: int) -> str:
    """1700 → '17,00 €'. Sempre due decimali, virgola come in Italia."""
    return f"{cent / 100:.2f} €".replace(".", ",")


# --- Le tabelle da mostrare nella pagina "Prezzi" --------------------------
# Sono dati, non logica: l'app le stampa così come sono.
INGRESSI = [
    {"tipo": "Ingresso giornaliero feriali", "residenti": 800, "non_residenti": 1100},
    {
        "tipo": "Ingresso giornaliero sabato, domenica e festivi",
        "residenti": 1000,
        "non_residenti": 1300,
    },
    {
        "tipo": "Ingresso giornata ridotta feriali (9–14 / 14–19)",
        "residenti": 600,
        "non_residenti": 900,
    },
    {
        "tipo": "Ingresso giornata ridotta sabato, domenica e festivi (9–14 / 14–19)",
        "residenti": 700,
        "non_residenti": 1000,
    },
    {"tipo": "Bambini 0–5 anni e disabili", "residenti": 0, "non_residenti": 0},
    {
        "tipo": "Bambini 6–10 anni e over 70",
        "residenti": 500,
        "non_residenti": 500,
    },
]

ABBONAMENTI = [
    {
        "tipo": "Settimanale",
        "validita": "7 giorni dalla data di attivazione",
        "residenti": 4600,
        "non_residenti": 6400,
        "vantaggio": "20% di sconto sul noleggio attrezzature",
    },
    {
        "tipo": "Mensile",
        "validita": "30 giorni dalla data di attivazione",
        "residenti": 16000,
        "non_residenti": 25000,
        "vantaggio": "30% di sconto sul noleggio attrezzature",
    },
]

NOLEGGIO = [
    {
        "tipo": "Ombrellone",
        "lettini": 0,
        "intera": 500,
        "abbonato_settimanale": 400,
        "abbonato_mensile": 300,
    },
    {
        "tipo": "Lettino",
        "lettini": None,
        "intera": 500,
        "abbonato_settimanale": 400,
        "abbonato_mensile": 300,
    },
    {
        "tipo": "Postazione Relax 1 — 1 ombrellone + 1 lettino",
        "lettini": 1,
        "intera": 700,
        "abbonato_settimanale": 500,
        "abbonato_mensile": 400,
    },
    {
        "tipo": "Postazione Relax 2 — 1 ombrellone + 2 lettini",
        "lettini": 2,
        "intera": 1200,
        "abbonato_settimanale": 900,
        "abbonato_mensile": 800,
    },
    {
        "tipo": "Postazione Relax 3 — 1 ombrellone + 3 lettini",
        "lettini": 3,
        "intera": 1700,
        "abbonato_settimanale": 1300,
        "abbonato_mensile": 1100,
    },
]

# Il noleggio non è compreso nell'ingresso: sta scritto sul cartello e va
# ripetuto nell'app, altrimenti qualcuno arriva in cassa convinto del contrario.
NOTE_LISTINO = [
    "Il noleggio delle attrezzature non è compreso nel biglietto d'ingresso.",
    "Le tariffe scontate sul noleggio valgono solo per chi ha l'abbonamento.",
    "Le tariffe d'ingresso sono quelle comunali.",
]
