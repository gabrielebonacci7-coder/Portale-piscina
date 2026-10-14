"""Il promemoria del giorno prima.

Un giro ogni pochi minuti: chi ha una lezione che comincia entro
`ore_promemoria` ore e non ha ancora avuto il promemoria, lo riceve, come
notifica nell'app e per email. Ogni prenotazione lo riceve una volta sola
(`promemoria_il`).

Chi prenota all'ultimo momento, quando mancano meno di due ore, non lo
riceve: se l'è appena segnato da sola, un messaggio adesso sarebbe solo
rumore.
"""

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from reformer.core import email as posta
from reformer.core.config import settings
from reformer.db.session import SessionLocal
from reformer.dominio import orario
from reformer.models import Lezione, Prenotazione, StatoPrenotazione
from reformer.servizi.regole import notifica

log = logging.getLogger("reformer.promemoria")

OGNI_SECONDI = 300


def manda_promemoria(db: Session) -> int:
    adesso = orario.adesso()
    entro = adesso + timedelta(hours=settings.ore_promemoria)
    da_avvisare = db.scalars(
        select(Prenotazione)
        .join(Lezione)
        .where(
            Prenotazione.stato == StatoPrenotazione.ATTIVA,
            Prenotazione.promemoria_il.is_(None),
            Lezione.annullata_il.is_(None),
            Lezione.inizio > adesso + timedelta(hours=2),
            Lezione.inizio <= entro,
        )
        .options(joinedload(Prenotazione.lezione), joinedload(Prenotazione.utente))
    ).all()
    for p in da_avvisare:
        ist = orario.ISTRUTTRICI[p.lezione.istruttrice]["nome"]
        quando = orario.quando(p.lezione.inizio)
        notifica(db, p.utente_id, f"Promemoria: lezione di {quando} con {ist}. Ti aspettiamo!")
        posta.email_promemoria(p.utente.email, p.utente.nome, quando, ist)
        p.promemoria_il = adesso
        db.commit()
    return len(da_avvisare)


async def giro_continuo() -> None:
    while True:
        try:
            with SessionLocal() as db:
                n = await asyncio.to_thread(manda_promemoria, db)
                if n:
                    log.info("Promemoria mandati: %d", n)
        except Exception:  # noqa: BLE001 - il giro non deve fermarsi per un errore
            log.exception("Giro dei promemoria non riuscito")
        await asyncio.sleep(OGNI_SECONDI)
