"""I dati della piscina e le parole che l'app dice a chi entra.

È il file da aprire quando cambia un numero di telefono, un orario o una
frase di benvenuto: nessuna di queste cose sta scritta dentro le pagine.

⚠️  Le voci segnate DA CONFERMARE vanno riempite con i dati veri prima di
    andare online: sono le uniche informazioni che non stavano né sul cartello
    del listino né sulla piantina.
"""

NOME = "Piscina Comunale di Ciampino"
GESTORE = "ASD Accademia del Nuoto Marino"
COMUNE = "Città di Ciampino — Città Metropolitana di Roma Capitale"

TELEFONO = "+39 329 683 6522"          # dal cartello del listino
TELEFONO_COMPATTO = "+393296836522"    # per il link "chiama"

# DA CONFERMARE: via e numero civico esatti.
INDIRIZZO = "Ciampino (RM)"
# Finché l'indirizzo esatto non c'è, la ricerca per nome porta comunque al
# posto giusto su tutte le mappe.
RICERCA_MAPPE = "Piscina Comunale Ciampino"

ORARI = "Tutti i giorni, dalle 9:00 alle 19:00"
STAGIONE = "Stagione estiva 2026"

# DA CONFERMARE: mezzi pubblici e parcheggio.
COME_ARRIVARE = [
    {
        "titolo": "In auto",
        "testo": "Si arriva da Ciampino centro. Parcheggio nelle strade "
                 "attorno alla struttura.",
    },
    {
        "titolo": "Con i mezzi",
        "testo": "Stazione FL4/FL6 di Ciampino e autobus urbani; "
                 "fermata più vicina a pochi minuti a piedi.",
    },
]

# --- Il benvenuto ----------------------------------------------------------
# Quello che dice l'omino la prima volta che si apre l'app. Frasi corte: sono
# fumetti, non un regolamento. Si cambiano qui e cambiano ovunque.
#
# DA CONFERMARE: il testo vero. Questo è una bozza, scritta per far vedere
# come funziona.
BENVENUTO = {
    "nome": "Gabriele",
    "ruolo": "Piscina Comunale di Ciampino",
    "battute": [
        "Ciao, benvenuto alla Piscina Comunale di Ciampino!",
        "Da qui scegli il tuo posto sulla mappa: ombrellone, lettini, "
        "giornata intera o mezza giornata.",
        "In verde c'è quello che è ancora libero. Prenoti in un minuto e "
        "paghi comodamente in cassa quando arrivi.",
    ],
    "invito": "Scegli il posto",
}

# --- La legenda dei colori -------------------------------------------------
# Vive qui perché è una regola della struttura, non una scelta grafica: se un
# domani si aggiunge una terza fascia, la legenda cambia insieme alle regole.
LEGENDA = [
    {"stato": "libera", "testo": "Libera tutto il giorno"},
    {"stato": "mezza", "testo": "Libera solo mattina o solo pomeriggio"},
    {"stato": "occupata", "testo": "Occupata"},
    {"stato": "spenta", "testo": "Non disponibile"},
]


def scheda() -> dict:
    """Tutto quello che serve alle pagine "Dove siamo" e al benvenuto."""
    return {
        "nome": NOME,
        "gestore": GESTORE,
        "comune": COMUNE,
        "telefono": TELEFONO,
        "telefono_compatto": TELEFONO_COMPATTO,
        "indirizzo": INDIRIZZO,
        "ricerca_mappe": RICERCA_MAPPE,
        "orari": ORARI,
        "stagione": STAGIONE,
        "come_arrivare": COME_ARRIVARE,
        "benvenuto": BENVENUTO,
        "legenda": LEGENDA,
    }
