"""Limite ai tentativi ripetuti.

Due cose vanno protette: l'accesso allo staff (altrimenti si prova la password
all'infinito) e il modulo di prenotazione, che è aperto a chiunque e senza un
tetto si riempie di cinquanta prenotazioni finte in un minuto.

I contatori stanno in memoria, non nel database: nessun pezzo in più da
installare e nessuna scrittura su disco a ogni tentativo. Riavviando si
azzerano — accettabile, perché un riavvio non è una cosa che un estraneo può
provocare a comando.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request

from piscina.core.config import settings

_tentativi: dict[str, list[float]] = defaultdict(list)
_prossima_pulizia = 0.0
INTERVALLO_PULIZIA = 600


def _finestra() -> float:
    return settings.finestra_limiti_minuti * 60


def _pulisci(adesso: float) -> None:
    global _prossima_pulizia
    if adesso < _prossima_pulizia:
        return
    _prossima_pulizia = adesso + INTERVALLO_PULIZIA
    limite = adesso - _finestra()
    for chiave in list(_tentativi):
        recenti = [t for t in _tentativi[chiave] if t > limite]
        if recenti:
            _tentativi[chiave] = recenti
        else:
            del _tentativi[chiave]


def ip_richiedente(request: Request) -> str:
    """L'IP di chi chiama, tenendo conto del proxy davanti.

    `X-Forwarded-For` si legge solo se `PISCINA_DIETRO_PROXY` è attivo:
    quando l'app è esposta diretta, quell'intestazione se la scrive il client.
    """
    if settings.dietro_proxy:
        inoltrato = request.headers.get("x-forwarded-for")
        if inoltrato:
            return inoltrato.split(",")[0].strip()
    return request.client.host if request.client else "sconosciuto"


def controlla(chiave: str, massimo: int, messaggio: str) -> None:
    """Registra un tentativo e blocca se sono troppi nella finestra."""
    adesso = time.monotonic()
    _pulisci(adesso)
    recenti = [t for t in _tentativi[chiave] if t > adesso - _finestra()]
    if len(recenti) >= massimo:
        raise HTTPException(status_code=429, detail=messaggio)
    recenti.append(adesso)
    _tentativi[chiave] = recenti


def azzera(chiave: str) -> None:
    """Dopo un accesso riuscito i tentativi falliti non contano più."""
    _tentativi.pop(chiave, None)


def azzera_tutto() -> None:
    """Solo per i test."""
    _tentativi.clear()
