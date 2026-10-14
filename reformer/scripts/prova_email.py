"""Le email partono? Questo lo dice, in italiano.

    python -m reformer.scripts.prova_email tua@email.it

Sul server: `docker compose exec app python -m reformer.scripts.prova_email tua@email.it`
"""

import smtplib
import socket
import sys

from reformer.core import email as posta
from reformer.core.config import settings

SPIEGAZIONI = [
    (smtplib.SMTPAuthenticationError,
     "Gmail ha rifiutato utente o password. Serve la «password per le app» di 16 lettere "
     "(non la password normale) e la verifica in due passaggi attiva sull'account."),
    (socket.gaierror, "Il nome del server SMTP non esiste: controlla REFORMER_EMAIL_SMTP_HOST."),
    (TimeoutError, "Il server SMTP non risponde: porta sbagliata o rete del server che la blocca."),
    (ConnectionRefusedError, "Connessione rifiutata: controlla porta (587) e host."),
]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    if not settings.email_smtp_host:
        print("REFORMER_EMAIL_SMTP_HOST è vuoto: le email finiscono solo nel log. Compila il file .env.")
        return 1
    print(f"Provo a spedire da {settings.email_smtp_utente} via {settings.email_smtp_host}:{settings.email_smtp_porta}…")
    try:
        posta._spedisci_smtp(_messaggio(sys.argv[1]))
    except Exception as e:  # noqa: BLE001
        for tipo, testo in SPIEGAZIONI:
            if isinstance(e, tipo):
                print(f"Non è partita. {testo}\n(dettaglio: {e})")
                return 1
        print(f"Non è partita: {e}")
        return 1
    print("Partita! Controlla la casella (e lo spam).")
    return 0


def _messaggio(a: str):
    from email.message import EmailMessage

    m = EmailMessage()
    m["From"] = settings.email_mittente
    m["To"] = a
    m["Subject"] = "Prova — RE FORMER"
    m.set_content("Se leggi questo messaggio, le email di RE FORMER funzionano." + posta.FIRMA)
    return m


if __name__ == "__main__":
    sys.exit(main())
