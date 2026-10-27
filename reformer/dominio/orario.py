"""L'orario della settimana e chi insegna.

È il solo posto da toccare se cambia l'orario: le lezioni del calendario si
creano seguendo queste righe.
"""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from reformer.core.config import settings

FUSO = ZoneInfo(settings.fuso_orario)

# Giorno della settimana (lunedì = 0, come date.weekday()) → orari d'inizio.
ORARIO: dict[int, list[time]] = {
    0: [time(15, 30), time(16, 30), time(17, 30)],
    1: [time(15, 30), time(16, 30), time(17, 30)],
    2: [time(15, 30), time(16, 30), time(17, 30)],
    3: [time(15, 30), time(16, 30), time(17, 30)],
    4: [time(15, 30), time(16, 30), time(17, 30)],
    5: [time(11, 30), time(12, 30)],
}
DURATA_MINUTI = 60

# Il nome di partenza di alcune lezioni fisse. Greta ed Elisa possono
# cambiarlo dal gestionale ("tutte le settimane"): quella scelta vince su
# questa tabella. Le altre lezioni si chiamano "Reformer".
TITOLI_INIZIALI: dict[tuple[int, str], str] = {
    (0, "16:30"): "Pilates fitness",   # lunedì
    (2, "16:30"): "Pilates fitness",   # mercoledì
}
TITOLO_BASE = "Reformer"

# Oltre all'orario fisso, Greta ed Elisa possono aprire una lezione in più dal
# gestionale (per esempio alle 18:30): ORARIO_EXTRA_SUGGERITO è l'ora che il
# gestionale propone, giorno per giorno.
ORARIO_EXTRA_SUGGERITO = {0: "18:30", 1: "18:30", 2: "18:30", 3: "18:30", 4: "18:30", 5: "13:30"}

ISTRUTTRICI = {
    "greta": {"id": "greta", "nome": "Greta", "cognome": "Lorenzetti"},
    "elisa": {"id": "elisa", "nome": "Elisa", "cognome": "Bonacci"},
}

# Lunedì, mercoledì, venerdì e sabato Greta; martedì e giovedì Elisa.
ISTRUTTRICE_DEL_GIORNO = {0: "greta", 1: "elisa", 2: "greta", 3: "elisa", 4: "greta", 5: "greta"}


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
    return [inizio_utc(giorno, ora) for ora in ORARIO.get(giorno.weekday(), [])]


def giorni(da: date, quanti: int) -> list[date]:
    return [da + timedelta(days=i) for i in range(quanti)]


def ultimo_giorno_prenotabile() -> date:
    return oggi() + timedelta(days=settings.giorni_prenotabili)


GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def quando(istante: datetime) -> str:
    """"martedì 14 ottobre alle 17:30" — per notifiche ed email."""
    t = locale(istante)
    return f"{GIORNI[t.weekday()]} {t.day} {MESI[t.month - 1]} alle {t:%H:%M}"
