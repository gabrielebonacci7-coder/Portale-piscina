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
# Non è un testo unico ma una piccola guida: un paragrafo alla volta, e a ogni
# paragrafo l'app mostra la sezione di cui si sta parlando (`vetrina`).
#
# `{nome}` diventa il nome di chi sta usando l'app — quello lasciato con
# l'ultima prenotazione su quel telefono. Chi non l'ha mai lasciato viene
# accolto con il saluto generico: per questo il primo passo ha due versioni.
BENVENUTO = {
    "passi": [
        {
            "testo": "Buongiorno a tutti, benvenuti nel nuovo portale di "
                     "prenotazione della Piscina Comunale di Ciampino.",
            "testo_con_nome": "Buongiorno {nome}, benvenuto nel nuovo portale "
                              "di prenotazione della Piscina Comunale di Ciampino.",
        },
        {
            "testo": "Quante volte vi è capitato di arrivare in piscina e non "
                     "trovare la postazione che desideravate — o di trovare "
                     "tutto pieno?",
        },
        {
            "testo": "Questo portale nasce proprio per togliervi questo pensiero.",
        },
        {
            "testo": "Con due tocchi prenoti i lettini e gli ombrelloni che "
                     "vuoi, esattamente dove vuoi tu.",
            "vetrina": "mappa",
        },
        {
            "testo": "Qui trovi anche tutti i prezzi e i pacchetti che "
                     "mettiamo a disposizione.",
            "vetrina": "prezzi",
        },
        {
            "testo": "E se ti serve qualcosa, scrivi direttamente alla piscina.",
            "vetrina": "contatti",
        },
        {
            "testo": "Cosa aspetti? Prenota subito la tua prossima giornata "
                     "in piscina.",
        },
    ],
    "invito": "Prenota adesso",
}

# Ricompare a prenotazione fatta, per ringraziare.
GRAZIE = {
    "passi": [
        {"testo": "Grazie {nome}! La tua postazione è prenotata."},
        {"testo": "Ti aspettiamo in piscina: il noleggio si paga in cassa "
                  "quando arrivi."},
    ],
    "invito": "Vedi il codice",
}

# --- Come ci si scrive ------------------------------------------------------
# La chat con la piscina passa da WhatsApp: è il posto dove lo staff risponde
# già oggi, dal telefono che ha in tasca. Una chat dentro l'app vorrebbe dire
# che qualcuno la deve guardare, e una chat che nessuno guarda è peggio di non
# averla.
CONTATTI = {
    "whatsapp": "393296836522",
    "messaggio_precompilato": "Buongiorno! Scrivo dal portale delle prenotazioni.",
    "email": "",  # DA CONFERMARE: l'indirizzo pubblico della piscina
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
        "contatti": CONTATTI,
        "legenda": LEGENDA,
    }
