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

INDIRIZZO = "Via Superga — Ciampino (RM)"
RIFERIMENTO = "accanto al campo sportivo comunale"
# Con che parole cercarla nelle mappe del telefono.
RICERCA_MAPPE = "Piscina Comunale Ciampino Via Superga"

ORARI = "Tutti i giorni, dalle 9:00 alle 19:00"
STAGIONE = "Stagione estiva 2026"

# DA CONFERMARE: quale autobus e dove ferma.
COME_ARRIVARE = [
    {
        "titolo": "In auto",
        "testo": "Via Superga, accanto al campo sportivo comunale.",
    },
    {
        "titolo": "Dove si parcheggia",
        "testo": "C'è il parcheggio interno della struttura. Quando è pieno, "
                 "quello del cimitero è a due passi.",
    },
    {
        "titolo": "Con i mezzi",
        "testo": "Stazione FL4/FL6 di Ciampino e autobus urbani, "
                 "poi pochi minuti a piedi.",
    },
]

# --- Quello che dice l'omino ----------------------------------------------
# Frasi corte: sono fumetti, non un regolamento. Si cambiano qui e cambiano in
# tutta l'app.
#
# `{nome}` diventa il nome di chi sta usando l'app — quello lasciato con
# l'ultima prenotazione su quel telefono. Se non lo sappiamo ancora, sparisce
# insieme allo spazio che ha davanti: "Buongiorno!" e non "Buongiorno !".
BENVENUTO = {
    "battute": [
        "Buongiorno {nome}! Che splendida giornata per un bagno in piscina.",
        "Siamo felici che ci abbiate scelto. Scegli il posto che preferisci: "
        "al resto pensiamo noi.",
    ],
    "invito": "Scegli il posto",
}

# Ricompare a prenotazione fatta, per ringraziare.
GRAZIE = {
    "battute": [
        "Grazie {nome}! La tua postazione è prenotata.",
        "Ti aspettiamo in piscina: il noleggio si paga in cassa quando arrivi.",
    ],
    "invito": "Vedi il codice",
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
        "riferimento": RIFERIMENTO,
        "ricerca_mappe": RICERCA_MAPPE,
        "orari": ORARI,
        "stagione": STAGIONE,
        "come_arrivare": COME_ARRIVARE,
        "benvenuto": BENVENUTO,
        "grazie": GRAZIE,
        "legenda": LEGENDA,
    }
