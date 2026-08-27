"""Importare questo modulo registra tutte le tabelle su Base.metadata."""

from piscina.db.base import Base
from piscina.models.operatore import Operatore
from piscina.models.postazione import Postazione
from piscina.models.prenotazione import (
    ANNULLATA,
    ARRIVATO,
    IN_ATTESA,
    MATTINA,
    MEZZE,
    POMERIGGIO,
    STATI,
    Occupazione,
    Prenotazione,
    RigaPrenotazione,
)

__all__ = [
    "ANNULLATA",
    "ARRIVATO",
    "IN_ATTESA",
    "MATTINA",
    "MEZZE",
    "POMERIGGIO",
    "STATI",
    "Base",
    "Occupazione",
    "Operatore",
    "Postazione",
    "Prenotazione",
    "RigaPrenotazione",
]
