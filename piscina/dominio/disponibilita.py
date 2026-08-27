"""Le fasce orarie e la regola che dice quando due prenotazioni litigano."""

from datetime import date, datetime, time

from piscina.core.config import settings

GIORNATA = "giornata"
MATTINA = "mattina"
POMERIGGIO = "pomeriggio"

FASCE = (GIORNATA, MATTINA, POMERIGGIO)

# Le mezze giornate del listino: 9–14 e 14–19.
ETICHETTE = {
    GIORNATA: "Giornata intera",
    MATTINA: "Mattina",
    POMERIGGIO: "Pomeriggio",
}


def orario(fascia: str) -> tuple[time, time]:
    if fascia == MATTINA:
        return settings.ora_apertura, settings.ora_cambio_fascia
    if fascia == POMERIGGIO:
        return settings.ora_cambio_fascia, settings.ora_chiusura
    return settings.ora_apertura, settings.ora_chiusura


def orario_esteso(fascia: str) -> str:
    inizio, fine = orario(fascia)
    return f"{inizio:%H:%M}–{fine:%H:%M}"


def si_sovrappongono(a: str, b: str) -> bool:
    """Due fasce sullo stesso giorno si escludono a vicenda?

    La giornata intera copre tutto, quindi litiga con chiunque. Mattina e
    pomeriggio invece convivono: è tutto il senso della mezza giornata.
    """
    if GIORNATA in (a, b):
        return True
    return a == b


def fasce_in_conflitto(fascia: str) -> tuple[str, ...]:
    """Le fasce già prenotate che impediscono di prendere questa."""
    return tuple(f for f in FASCE if si_sovrappongono(f, fascia))


def fascia_conclusa(giorno: date, fascia: str, adesso: datetime) -> bool:
    """La fascia è già finita? Non si prenota un pomeriggio alle otto di sera."""
    if giorno > adesso.date():
        return False
    if giorno < adesso.date():
        return True
    _, fine = orario(fascia)
    return adesso.time() >= fine
