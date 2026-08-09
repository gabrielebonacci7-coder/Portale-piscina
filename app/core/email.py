"""Invio delle email.

In sviluppo non si spedisce niente: il messaggio finisce nel log, con il link
in chiaro, così si prova tutto il giro senza configurare nulla.

In produzione si imposta `EMAIL_SMTP_HOST` (più utente, password e porta) e le
email partono davvero. Il resto del codice non cambia: chiama sempre
`invia_email(...)` e non sa quale delle due strade viene presa.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger("guardlink.email")


class ErroreInvio(RuntimeError):
    """L'email non è partita. Chi chiama decide se è un guaio o no."""


def _spedisci_smtp(messaggio: EmailMessage) -> None:
    porta = settings.email_smtp_porta
    # 465 è SMTPS (cifrato da subito), 587 è STARTTLS (si cifra dopo).
    classe = smtplib.SMTP_SSL if porta == 465 else smtplib.SMTP
    with classe(settings.email_smtp_host, porta, timeout=20) as server:
        if porta != 465:
            server.starttls()
        if settings.email_smtp_utente:
            server.login(settings.email_smtp_utente, settings.email_smtp_password)
        server.send_message(messaggio)


def invia_email(destinatario: str, oggetto: str, testo: str) -> None:
    """Spedisce un'email, o la scrive nel log se l'SMTP non è configurato."""
    messaggio = EmailMessage()
    messaggio["From"] = settings.email_mittente
    messaggio["To"] = destinatario
    messaggio["Subject"] = oggetto
    messaggio.set_content(testo)

    if not settings.email_smtp_host:
        # Riga sola e ben riconoscibile: in sviluppo si cerca "EMAIL" nel log
        # e si copia il link dal terminale.
        log.warning(
            "EMAIL non spedita (SMTP non configurato) → a: %s | oggetto: %s\n%s",
            destinatario, oggetto, testo,
        )
        return

    try:
        _spedisci_smtp(messaggio)
    except Exception as e:  # noqa: BLE001 - qualsiasi guasto SMTP va riportato uguale
        log.error("Invio email a %s fallito: %s", destinatario, e)
        raise ErroreInvio(str(e)) from e


# --- I messaggi ------------------------------------------------------------
def email_verifica(destinatario: str, link: str) -> None:
    invia_email(
        destinatario,
        "Conferma il tuo indirizzo — Guardlink",
        "Ciao,\n\n"
        "per confermare il tuo indirizzo su Guardlink apri questo link:\n\n"
        f"{link}\n\n"
        f"Il link vale {settings.ore_validita_verifica} ore.\n"
        "Se non ti sei iscritto tu, ignora questo messaggio.\n\n"
        "— Guardlink\n",
    )


def email_recupero(destinatario: str, link: str) -> None:
    invia_email(
        destinatario,
        "Reimposta la password — Guardlink",
        "Ciao,\n\n"
        "hai chiesto di reimpostare la password di Guardlink. Apri questo link:\n\n"
        f"{link}\n\n"
        f"Il link vale {settings.minuti_validita_recupero} minuti e si usa una volta sola.\n"
        "Se non sei stato tu, non devi fare niente: la password resta quella di prima.\n\n"
        "— Guardlink\n",
    )
