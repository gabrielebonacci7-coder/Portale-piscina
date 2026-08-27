"""Invio delle email.

In sviluppo non parte niente: il messaggio finisce nel log, così si prova
tutto il giro senza configurare un server SMTP. Online si impostano
`PISCINA_EMAIL_SMTP_HOST` e compagnia, e le email partono davvero.

Sono due messaggi soli, e fanno due mestieri diversi:

- allo **staff** arriva la prenotazione con nome, telefono ed email: è questo
  il filo che collega il modulo sul telefono del cliente al banco della cassa;
- al **cliente** arriva la conferma con il codice e i posti scelti.
"""

import logging
import smtplib
from email.message import EmailMessage
from typing import TYPE_CHECKING

from piscina.core.config import settings
from piscina.dominio import disponibilita, listino

if TYPE_CHECKING:
    from piscina.models import Prenotazione

log = logging.getLogger("piscina.email")


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
    messaggio = EmailMessage()
    messaggio["From"] = settings.email_mittente
    messaggio["To"] = destinatario
    messaggio["Subject"] = oggetto
    messaggio.set_content(testo)

    if not settings.email_smtp_host:
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
def _riepilogo_posti(prenotazione: "Prenotazione") -> str:
    righe = []
    for r in sorted(prenotazione.righe, key=lambda r: r.postazione.codice):
        if r.postazione.tipo == "lettino":
            dettaglio = "lettino solarium"
        elif r.lettini:
            dettaglio = f"ombrellone + {r.lettini} letti{'no' if r.lettini == 1 else 'ni'}"
        else:
            dettaglio = "solo ombrellone"
        righe.append(f"  · {r.postazione.codice} — {dettaglio} — {listino.euro(r.prezzo_cent)}")
    return "\n".join(righe)


def _intestazione(prenotazione: "Prenotazione") -> str:
    fascia = disponibilita.ETICHETTE[prenotazione.fascia]
    ore = disponibilita.orario_esteso(prenotazione.fascia)
    return (
        f"Codice: {prenotazione.codice}\n"
        f"Giorno: {prenotazione.giorno:%d/%m/%Y}\n"
        f"Fascia: {fascia} ({ore})\n"
        f"Persone: {prenotazione.persone}\n"
    )


def email_staff_nuova_prenotazione(prenotazione: "Prenotazione") -> None:
    """La prenotazione appena arrivata, con i contatti del cliente."""
    destinatari = settings.destinatari_staff
    if not destinatari:
        log.warning(
            "Nessun destinatario staff configurato (PISCINA_EMAIL_STAFF): "
            "la prenotazione %s non è stata segnalata via email.",
            prenotazione.codice,
        )
        return

    testo = (
        "Nuova prenotazione dal sito.\n\n"
        + _intestazione(prenotazione)
        + f"\nCliente: {prenotazione.nome}\n"
        f"Telefono: {prenotazione.telefono}\n"
        f"Email: {prenotazione.email}\n"
        + (f"Note: {prenotazione.note}\n" if prenotazione.note else "")
        + "\nPostazioni:\n"
        + _riepilogo_posti(prenotazione)
        + f"\n\nTotale noleggio da incassare: {listino.euro(prenotazione.totale_cent)}\n"
        "(gli ingressi si contano in cassa)\n\n"
        f"Gestionale: {settings.url_pubblico}/staff\n"
    )
    oggetto = (
        f"Prenotazione {prenotazione.codice} — {prenotazione.giorno:%d/%m} "
        f"{disponibilita.ETICHETTE[prenotazione.fascia].lower()} — {prenotazione.nome}"
    )
    for destinatario in destinatari:
        invia_email(destinatario, oggetto, testo)


def email_cliente_conferma(prenotazione: "Prenotazione") -> None:
    """La conferma per chi ha prenotato: codice, posti, cosa portare in cassa."""
    testo = (
        f"Ciao {prenotazione.nome.split()[0] if prenotazione.nome else ''},\n\n"
        "la tua prenotazione alla Piscina Comunale di Ciampino è registrata.\n\n"
        + _intestazione(prenotazione)
        + "\nPostazioni:\n"
        + _riepilogo_posti(prenotazione)
        + f"\n\nTotale noleggio: {listino.euro(prenotazione.totale_cent)}\n"
        "Si paga in cassa all'arrivo, insieme al biglietto d'ingresso "
        "(il noleggio non è compreso nell'ingresso).\n\n"
        f"Per modificare o annullare: {settings.url_pubblico}/#/prenotazione "
        f"con il codice {prenotazione.codice} e il tuo numero di telefono.\n\n"
        "A presto!\n"
        "— Piscina Comunale di Ciampino\n"
    )
    invia_email(
        prenotazione.email,
        f"Prenotazione confermata — {prenotazione.codice}",
        testo,
    )


def email_cliente_annullata(prenotazione: "Prenotazione") -> None:
    invia_email(
        prenotazione.email,
        f"Prenotazione annullata — {prenotazione.codice}",
        f"La prenotazione {prenotazione.codice} del "
        f"{prenotazione.giorno:%d/%m/%Y} è stata annullata.\n\n"
        "Se non sei stato tu, chiamaci al 329 6836522.\n\n"
        "— Piscina Comunale di Ciampino\n",
    )


def email_staff_annullata(prenotazione: "Prenotazione") -> None:
    """Un posto si è liberato: lo staff deve saperlo senza aprire il gestionale."""
    destinatari = settings.destinatari_staff
    if not destinatari:
        return
    posti = ", ".join(prenotazione.codici_postazioni)
    testo = (
        "Prenotazione annullata dal cliente.\n\n"
        + _intestazione(prenotazione)
        + f"\nCliente: {prenotazione.nome} — {prenotazione.telefono}\n"
        f"Postazioni tornate libere: {posti}\n"
    )
    for destinatario in destinatari:
        invia_email(
            destinatario,
            f"Annullata {prenotazione.codice} — {prenotazione.giorno:%d/%m} — {posti}",
            testo,
        )
