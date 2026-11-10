"""L'orario della settimana e chi insegna.

È il solo posto da toccare se cambia l'orario: le lezioni del calendario si
creano seguendo queste righe.
"""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from reformer.core.config import settings

FUSO = ZoneInfo(settings.fuso_orario)

# Giorno della settimana (lunedì = 0, come date.weekday()) → orari d'inizio.
# Questo è l'orario NUOVO, in vigore dal NUOVO_ORARIO_DAL in poi.
ORARIO: dict[int, list[time]] = {
    0: [time(16, 30), time(17, 30)],                 # lunedì (Greta)
    1: [time(15, 30), time(16, 30)],                 # martedì (Elisa)
    2: [time(16, 30), time(17, 30)],                 # mercoledì (Greta)
    3: [time(15, 30), time(16, 30), time(17, 30)],   # giovedì (Elisa)
    4: [time(15, 30), time(16, 30)],                 # venerdì (Elisa)
    5: [time(11, 30)],                               # sabato (Greta)
}

# L'orario di prima: vale per i giorni prima del NUOVO_ORARIO_DAL, così le
# lezioni della settimana in corso (con le prenotazioni già fatte) non cambiano.
ORARIO_PRECEDENTE: dict[int, list[time]] = {
    **{g: [time(15, 30), time(16, 30), time(17, 30), time(18, 30)] for g in range(5)},
    5: [time(11, 30), time(12, 30)],
}

# Da questo lunedì (compreso) valgono l'orario nuovo e la chiusura delle
# prenotazioni a mezzanotte del giorno prima.
NUOVO_ORARIO_DAL = date(2026, 11, 16)


def ore_del(giorno: date) -> list[time]:
    """Gli orari d'inizio delle lezioni fisse di quel giorno."""
    tabella = ORARIO if giorno >= NUOVO_ORARIO_DAL else ORARIO_PRECEDENTE
    return tabella.get(giorno.weekday(), [])


DURATA_MINUTI = 60

# Il nome di partenza di alcune lezioni fisse. Greta ed Elisa possono
# cambiarlo dal gestionale ("tutte le settimane"): quella scelta vince su
# questa tabella. Le altre lezioni si chiamano "Pilates".
TITOLI_INIZIALI: dict[tuple[int, str], str] = {
    (0, "16:30"): "Pilates fitness",   # lunedì
    (2, "16:30"): "Pilates fitness",   # mercoledì
}
TITOLO_BASE = "Pilates"

# Oltre all'orario fisso, Greta ed Elisa possono aprire una lezione in più dal
# gestionale (per esempio alle 19:30): ORARIO_EXTRA_SUGGERITO è l'ora che il
# gestionale propone, giorno per giorno.
ORARIO_EXTRA_SUGGERITO = {0: "18:30", 1: "17:30", 2: "18:30", 3: "18:30", 4: "17:30", 5: "12:30"}

ISTRUTTRICI = {
    "elisa": {"id": "elisa", "nome": "Elisa", "cognome": "Bonacci"},
    "greta": {"id": "greta", "nome": "Greta", "cognome": "Lorenzetti"},
}

# Lunedì, mercoledì e sabato Greta; martedì, giovedì e venerdì Elisa.
ISTRUTTRICE_DEL_GIORNO = {0: "greta", 1: "elisa", 2: "greta", 3: "elisa", 4: "elisa", 5: "greta"}

# Scambi di un giorno solo, che valgono al posto della regola della settimana
# ("AAAA-MM-GG": chi insegna quel giorno). Si tolgono pure quando sono passati.
ECCEZIONI_ISTRUTTRICE = {
    "2026-11-20": "greta",   # venerdì
    "2026-11-21": "elisa",   # sabato
    "2026-11-27": "greta",   # venerdì
}


def istruttrice_del(giorno) -> str:
    """Chi insegna in quel giorno (una `date`): l'eccezione, se c'è, o la regola."""
    return ECCEZIONI_ISTRUTTRICE.get(giorno.isoformat()) or ISTRUTTRICE_DEL_GIORNO[giorno.weekday()]


def adesso() -> datetime:
    return datetime.now(timezone.utc)


def oggi() -> date:
    """Oggi a Roma, non a Greenwich: a mezzanotte e mezza è già domani."""
    return adesso().astimezone(FUSO).date()


def inizio_utc(giorno: date, ora: time) -> datetime:
    """L'istante d'inizio di una lezione, dall'orario locale di Roma.

    Passa per il fuso così l'ora legale è giusta da sola: le 16:30 restano le
    16:30 anche dopo il cambio d'ora.
    """
    return datetime.combine(giorno, ora, tzinfo=FUSO).astimezone(timezone.utc)


def locale(istante: datetime) -> datetime:
    return istante.astimezone(FUSO)


def orari_del_giorno(giorno: date) -> list[datetime]:
    return [inizio_utc(giorno, ora) for ora in ore_del(giorno)]


def giorni(da: date, quanti: int) -> list[date]:
    return [da + timedelta(days=i) for i in range(quanti)]


def ultimo_giorno_prenotabile() -> date:
    return oggi() + timedelta(days=settings.giorni_prenotabili)


def primo_giorno_prenotabile() -> date:
    """Le prenotazioni si chiudono a mezzanotte del giorno prima: la lezione di
    oggi non si prenota più (con 0 giorni, si prenota fino all'inizio)."""
    return oggi() + timedelta(days=settings.giorni_chiusura_prenotazioni)


# Le lezioni create prima di questa data seguivano l'orario precedente: quelle
# future che non stanno nell'orario nuovo vengono tolte all'avvio. Quelle create
# dopo (le lezioni in più aperte dal gestionale) non si toccano.
ORARIO_VALIDO_DAL = datetime(2026, 11, 14, tzinfo=timezone.utc)


GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def quando(istante: datetime) -> str:
    """"martedì 14 ottobre alle 17:30" — per notifiche ed email."""
    t = locale(istante)
    return f"{GIORNI[t.weekday()]} {t.day} {MESI[t.month - 1]} alle {t:%H:%M}"
