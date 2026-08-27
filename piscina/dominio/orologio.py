"""Che ore sono in piscina.

Il server può stare su UTC, e alle 23:30 di un martedì italiano per lui è già
mercoledì: "oggi" diventerebbe il giorno dopo e la prenotazione per domani
verrebbe rifiutata perché "nel passato". L'ora giusta è sempre quella di
Ciampino.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("Europe/Rome")


def adesso() -> datetime:
    return datetime.now(FUSO)


def oggi() -> date:
    return adesso().date()
