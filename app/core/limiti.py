"""Limite ai tentativi ripetuti su login, registrazione e recupero password.

Senza, chiunque può provare password all'infinito: una password da otto
caratteri comuni si indovina in poche ore se nessuno conta i tentativi. In
locale non conta niente, online sì.

**I limiti stanno in memoria**, non nel database. È la scelta giusta a questa
dimensione: nessun pezzo in più da installare, nessuna scrittura su disco a
ogni tentativo di accesso. Ha due conseguenze da sapere:

- riavviando l'applicazione i contatori si azzerano — accettabile, perché un
  riavvio non è una cosa che un estraneo può provocare a comando;
- con più processi uvicorn ogni processo ha i suoi contatori, quindi il limite
  effettivo si moltiplica per il numero di processi. Con due lavoratori un
  limite di 10 diventa 20: continua a fermare la forza bruta e non dà fastidio
  a nessuno. Se un giorno servisse un conteggio esatto, il posto dove metterlo
  è qui dentro (Redis), senza toccare i router.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.core.config import settings

HTTP_429_TROPPI_TENTATIVI = 429

# chiave -> istanti dei tentativi, dal più vecchio.
_tentativi: dict[str, list[float]] = defaultdict(list)
# Ogni tanto si passa a ripulire, così la memoria non cresce all'infinito.
_prossima_pulizia = 0.0
INTERVALLO_PULIZIA = 600  # dieci minuti


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

    `X-Forwarded-For` si legge **solo** se `DIETRO_PROXY` è attivo: quando
    l'app è esposta direttamente, quell'intestazione se la scrive il client, e
    fidarsene vorrebbe dire lasciare che chiunque cambi identità a ogni
    tentativo — cioè non avere nessun limite.
    """
    if settings.dietro_proxy:
        inoltrato = request.headers.get("x-forwarded-for")
        if inoltrato:
            # Il primo della lista è il client originale.
            return inoltrato.split(",")[0].strip()
    return request.client.host if request.client else "sconosciuto"


def registra_tentativo(chiave: str, massimo: int) -> None:
    """Conta un tentativo e solleva 429 se si è oltre il massimo.

    Il conteggio avviene **prima** di sapere se il tentativo andrà a buon fine:
    è il tentativo in sé a costare, altrimenti provare mille password sbagliate
    sarebbe gratis.
    """
    adesso = time.monotonic()
    _pulisci(adesso)

    inizio_finestra = adesso - _finestra()
    recenti = [t for t in _tentativi[chiave] if t > inizio_finestra]

    if len(recenti) >= massimo:
        fra_quanto = int(recenti[0] + _finestra() - adesso) + 1
        _tentativi[chiave] = recenti
        raise HTTPException(
            HTTP_429_TROPPI_TENTATIVI,
            "Troppi tentativi. Riprova fra qualche minuto.",
            headers={"Retry-After": str(max(fra_quanto, 1))},
        )

    recenti.append(adesso)
    _tentativi[chiave] = recenti


def azzera(chiave: str) -> None:
    """Dimentica i tentativi di una chiave: si chiama quando l'accesso riesce.

    Chi entra con la password giusta non deve trascinarsi dietro gli errori di
    battitura di prima.
    """
    _tentativi.pop(chiave, None)


def svuota_tutto() -> None:
    """Solo per i test: riparte da zero fra un caso e l'altro."""
    _tentativi.clear()
    global _prossima_pulizia
    _prossima_pulizia = 0.0
