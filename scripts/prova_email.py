"""Prova la configurazione della posta mandando un'email vera.

    python -m scripts.prova_email tua@email.it

Serve perché l'app, di proposito, **non dice mai** se un'email è partita: al
recupero password risponde sempre "fatto", anche quando l'invio fallisce.
Deve essere così — un errore visibile rivelerebbe quali indirizzi sono
registrati — ma vuol dire che una configurazione sbagliata non si vede da
nessuna parte. Questo comando serve a vederla.

Non tocca il database e non crea nessun token: manda solo un messaggio di
prova.
"""

import argparse
import smtplib

from app.core import email as posta
from app.core.config import settings

# Errore SMTP → cosa vuol dire davvero, in italiano.
SPIEGAZIONI = [
    (
        smtplib.SMTPAuthenticationError,
        "Utente o password rifiutati.\n"
        "   Con Gmail la password del tuo account NON funziona: serve una\n"
        "   'password per le app', che si crea solo dopo aver attivato la\n"
        "   verifica in due passaggi. Vedi il README, sezione «Far partire le\n"
        "   email davvero».",
    ),
    (
        smtplib.SMTPSenderRefused,
        "Il server non accetta questo mittente.\n"
        "   Di solito EMAIL_MITTENTE deve contenere lo stesso indirizzo di\n"
        "   EMAIL_SMTP_UTENTE: non si può spedire a nome di un altro.",
    ),
    (
        smtplib.SMTPRecipientsRefused,
        "Il server ha rifiutato il destinatario: controlla l'indirizzo.",
    ),
    (
        smtplib.SMTPNotSupportedError,
        "Il server non offre la cifratura sulla porta indicata.\n"
        "   Prova EMAIL_SMTP_PORTA=465 (cifrata da subito) invece di 587.",
    ),
    (
        (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected),
        "Connessione al server di posta caduta.\n"
        "   Controlla EMAIL_SMTP_HOST e EMAIL_SMTP_PORTA.",
    ),
    (
        smtplib.SMTPException,
        "Il server di posta ha risposto con un errore.\n"
        "   Il codice qui sopra viene da lui: cercandolo insieme al nome del\n"
        "   servizio si trova quasi sempre la causa.",
    ),
    # Va per ultimo: gli errori SMTP qui sopra sono a loro volta OSError, e
    # chiamarli "server irraggiungibile" manderebbe fuori strada.
    (
        OSError,
        "Non si raggiunge il server di posta.\n"
        "   Controlla EMAIL_SMTP_HOST e EMAIL_SMTP_PORTA. Molte reti e molti\n"
        "   hosting bloccano la porta 587 in uscita: in quel caso prova la 465.",
    ),
]


def spiega(errore: BaseException) -> str:
    for tipi, testo in SPIEGAZIONI:
        if isinstance(errore, tipi):
            return testo
    return "Errore non previsto. Il messaggio qui sopra è quello del server."


def mostra_configurazione() -> bool:
    """Stampa come è configurata la posta. False se manca l'essenziale."""
    password = "(vuota)" if not settings.email_smtp_password else "•" * 12
    print("Configurazione attuale:")
    print(f"  EMAIL_SMTP_HOST      {settings.email_smtp_host or '(non impostato)'}")
    print(f"  EMAIL_SMTP_PORTA     {settings.email_smtp_porta}")
    print(f"  EMAIL_SMTP_UTENTE    {settings.email_smtp_utente or '(non impostato)'}")
    print(f"  EMAIL_SMTP_PASSWORD  {password}")
    print(f"  EMAIL_MITTENTE       {settings.email_mittente}")
    print(f"  URL_PUBBLICO         {settings.url_pubblico}")
    print()

    if not settings.email_smtp_host:
        print("EMAIL_SMTP_HOST non è impostato: l'app scrive le email nel log")
        print("invece di spedirle. Copia .env.esempio in .env e compilalo.")
        return False

    # Avvisi su cose che partono lo stesso ma non funzioneranno davvero.
    if settings.email_smtp_utente and settings.email_smtp_utente not in settings.email_mittente:
        print(f"! EMAIL_MITTENTE non contiene {settings.email_smtp_utente}.")
        print("  Quasi tutti i server rifiutano di spedire a nome di un altro,")
        print("  e Gmail riscrive comunque il mittente con il proprio indirizzo.\n")
    if "127.0.0.1" in settings.url_pubblico or "localhost" in settings.url_pubblico:
        print("! URL_PUBBLICO punta a questo computer.")
        print("  L'email partirà, ma il link dentro non si aprirà da nessun")
        print("  altro telefono. Va messo l'indirizzo pubblico dell'app.\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("destinatario", help="Indirizzo a cui mandare la prova")
    args = parser.parse_args()

    if not mostra_configurazione():
        return 1

    print(f"Invio un messaggio di prova a {args.destinatario}…")
    try:
        posta.invia_email(
            args.destinatario,
            "Prova di configurazione — Guardlink",
            "Se leggi questo messaggio, la posta di Guardlink funziona.\n\n"
            "Da adesso il recupero password e la conferma dell'indirizzo\n"
            "arrivano davvero agli iscritti.\n\n"
            "— Guardlink\n",
        )
    except posta.ErroreInvio as e:
        causa = e.__cause__ or e
        print(f"\nNON è partita: {causa}\n")
        print(f"   {spiega(causa)}")
        return 1

    print("\nPartita. Controlla la casella (guarda anche nello spam:")
    print("la prima email da un mittente nuovo ci finisce spesso).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
