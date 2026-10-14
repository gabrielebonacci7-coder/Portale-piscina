"""Account: registrazione, accesso, conferma email, recupero, cancellazione.

**Come Greta ed Elisa diventano staff.** I loro indirizzi stanno nella
configurazione (`REFORMER_EMAIL_STAFF`). Quando un account con uno di quegli
indirizzi **conferma l'email**, diventa staff da solo. La conferma è il
punto: registrarsi con l'indirizzo di Greta non basta, bisogna anche poter
leggere la sua posta.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from reformer.core import email as posta
from reformer.core.config import settings
from reformer.core.security import hash_password, verifica_password
from reformer.models import Ruolo, TipoToken, TokenEmail, Utente
from reformer.servizi.regole import ErroreRegola, notifica

log = logging.getLogger("reformer.account")

VERSIONE_PRIVACY = "2026-10"

DURATA = {
    TipoToken.VERIFICA_EMAIL: lambda: timedelta(hours=settings.ore_validita_verifica),
    TipoToken.RECUPERO_PASSWORD: lambda: timedelta(minutes=settings.minuti_validita_recupero),
}


def normalizza_email(email: str) -> str:
    return email.strip().lower()


def per_email(db: Session, email: str) -> Utente | None:
    return db.scalar(select(Utente).where(Utente.email == normalizza_email(email)))


# ------------------------------------------------------------------ token
def _impronta(codice: str) -> str:
    return hashlib.sha256(codice.encode("utf-8")).hexdigest()


def crea_token(db: Session, utente: Utente, tipo: TipoToken) -> str:
    """Genera un link monouso e ne restituisce il codice in chiaro, una volta
    sola: nel database resta solo l'impronta. I link precedenti dello stesso
    tipo smettono di valere."""
    adesso = datetime.now(timezone.utc)
    for vecchio in db.scalars(
        select(TokenEmail).where(
            TokenEmail.utente_id == utente.id, TokenEmail.tipo == tipo, TokenEmail.usato_il.is_(None)
        )
    ):
        vecchio.usato_il = adesso
    codice = secrets.token_urlsafe(32)
    db.add(
        TokenEmail(
            utente_id=utente.id, tipo=tipo, impronta=_impronta(codice),
            scade_il=adesso + DURATA[tipo](),
        )
    )
    db.commit()
    return codice


def _token_valido(db: Session, codice: str, tipo: TipoToken) -> TokenEmail:
    token = db.scalar(
        select(TokenEmail).where(TokenEmail.impronta == _impronta(codice or ""), TokenEmail.tipo == tipo)
    )
    if token is None or not token.valido:
        raise ErroreRegola("Il link non è più valido: chiedine uno nuovo.", 400)
    return token


def link(percorso: str, codice: str) -> str:
    # Il codice va nel frammento (#...): non finisce nei log del server né
    # nell'intestazione Referer se la pagina apre un link esterno.
    return f"{settings.url_pubblico.rstrip('/')}/#/{percorso}/{codice}"


# ---------------------------------------------------------------- staff
def aggiorna_ruolo(db: Session, utente: Utente) -> bool:
    """Dà il ruolo staff agli indirizzi configurati, se l'email è confermata.

    Si chiama alla conferma e a ogni accesso: così se un giorno si aggiunge un
    indirizzo nella configurazione, quella persona diventa staff al primo
    accesso, senza comandi. Ritorna True se il ruolo è cambiato.
    """
    if (
        utente.ruolo != Ruolo.STAFF
        and utente.email_verificata_il is not None
        and utente.email in settings.indirizzi_staff
    ):
        utente.ruolo = Ruolo.STAFF
        log.warning("Ruolo staff dato a %s (indirizzo nella configurazione)", utente.email)
        notifica(db, utente.id, "Benvenuta nel gestionale di RE FORMER: lo trovi nella barra in basso.")
        db.commit()
        return True
    return False


# ----------------------------------------------------------- registrazione
def registra(
    db: Session, *, nome: str, cognome: str, telefono: str, email: str, password: str
) -> Utente:
    email = normalizza_email(email)
    if per_email(db, email):
        raise ErroreRegola("Con questa email c'è già un account: prova ad accedere.", 409)
    utente = Utente(
        email=email,
        password_hash=hash_password(password),
        nome=nome.strip(),
        cognome=cognome.strip(),
        telefono=telefono.strip(),
        privacy_accettata_il=datetime.now(timezone.utc),
        versione_privacy=VERSIONE_PRIVACY,
    )
    db.add(utente)
    db.commit()
    notifica(
        db, utente.id,
        "Benvenuta! Puoi già prenotare. Le lezioni si pagano in studio: Greta o Elisa "
        "le caricano sul tuo account e le vedi in «Pacchetto».",
    )
    db.commit()
    invia_verifica(db, utente)
    return utente


def invia_verifica(db: Session, utente: Utente) -> None:
    if utente.email_verificata_il:
        return
    codice = crea_token(db, utente, TipoToken.VERIFICA_EMAIL)
    try:
        posta.email_verifica(utente.email, utente.nome, link("conferma", codice))
    except posta.ErroreInvio:
        # L'account esiste lo stesso: la cliente può prenotare, e il link si
        # può richiedere dal profilo quando la posta torna a funzionare.
        log.error("Email di conferma non partita per %s", utente.email)


def conferma_email(db: Session, codice: str) -> Utente:
    token = _token_valido(db, codice, TipoToken.VERIFICA_EMAIL)
    utente = token.utente
    token.usato_il = datetime.now(timezone.utc)
    if utente.email_verificata_il is None:
        utente.email_verificata_il = datetime.now(timezone.utc)
    db.commit()
    aggiorna_ruolo(db, utente)
    return utente


# ----------------------------------------------------------------- accesso
# Un hash vero, calcolato una volta: confrontarci contro una password quando
# l'email non esiste fa durare la risposta come per un account vero, così il
# tempo di risposta non rivela chi è iscritto.
_HASH_FINTO = hash_password("password-che-nessuno-ha")


def accedi(db: Session, email: str, password: str) -> Utente:
    utente = per_email(db, email)
    if utente is None or utente.cancellato_il is not None:
        verifica_password(password, _HASH_FINTO)
        raise ErroreRegola("Email o password non corrette.", 401)
    if not verifica_password(password, utente.password_hash):
        raise ErroreRegola("Email o password non corrette.", 401)
    aggiorna_ruolo(db, utente)
    return utente


# ----------------------------------------------------------------- password
def chiedi_recupero(db: Session, email: str) -> None:
    """Manda il link per una nuova password, se l'account esiste.

    Il chiamante risponde sempre allo stesso modo: dire "questa email non
    c'è" direbbe anche chi è cliente dello studio.
    """
    utente = per_email(db, email)
    if utente is None or utente.cancellato_il is not None:
        return
    codice = crea_token(db, utente, TipoToken.RECUPERO_PASSWORD)
    try:
        posta.email_recupero(utente.email, utente.nome, link("nuova-password", codice))
    except posta.ErroreInvio:
        log.error("Email di recupero non partita per %s", utente.email)


def nuova_password(db: Session, codice: str, password: str) -> Utente:
    token = _token_valido(db, codice, TipoToken.RECUPERO_PASSWORD)
    utente = token.utente
    token.usato_il = datetime.now(timezone.utc)
    utente.password_hash = hash_password(password)
    utente.sessione += 1  # esce da tutti gli altri telefoni
    # Ha letto la mail: l'indirizzo è suo.
    if utente.email_verificata_il is None:
        utente.email_verificata_il = datetime.now(timezone.utc)
    db.commit()
    aggiorna_ruolo(db, utente)
    return utente


def cambia_password(db: Session, utente: Utente, attuale: str, nuova: str) -> None:
    if not verifica_password(attuale, utente.password_hash):
        raise ErroreRegola("La password attuale non è giusta.", 400)
    utente.password_hash = hash_password(nuova)
    utente.sessione += 1
    db.commit()


# ------------------------------------------------------------------ privacy
def esporta(db: Session, utente: Utente) -> dict:
    """Tutto quello che lo studio sa di questa persona, in chiaro."""
    from reformer.dominio import orario  # import locale: evita il giro di import

    return {
        "account": {
            "nome": utente.nome, "cognome": utente.cognome, "email": utente.email,
            "telefono": utente.telefono, "iscritta_il": utente.creato_il.isoformat(),
            "email_confermata_il": utente.email_verificata_il.isoformat() if utente.email_verificata_il else None,
            "privacy_accettata_il": utente.privacy_accettata_il.isoformat() if utente.privacy_accettata_il else None,
            "lezioni_rimaste": utente.lezioni_rimaste,
            "scadenza": utente.scadenza.isoformat() if utente.scadenza else None,
        },
        "prenotazioni": [
            {"lezione": orario.quando(p.lezione.inizio), "stato": p.stato.value, "presente": p.presente}
            for p in utente.prenotazioni
        ],
    }


def cancella(db: Session, utente: Utente, password: str) -> None:
    """Cancella l'account su richiesta della cliente.

    Non è un DELETE: le prenotazioni passate servono allo studio per i conti
    (e alle altre clienti, che non devono vedersi spostare le liste). Si
    tolgono invece tutti i dati che identificano la persona.
    """
    from reformer.dominio import orario
    from reformer.models import Attesa, StatoPrenotazione
    from reformer.servizi import regole

    if not verifica_password(password, utente.password_hash):
        raise ErroreRegola("La password non è giusta.", 400)
    if utente.e_staff:
        raise ErroreRegola("Un account dello staff non si cancella da qui.", 400)
    adesso = orario.adesso()
    with regole._scrittura:
        # Le prenotazioni future si liberano: il posto va a chi è in attesa.
        for p in list(utente.prenotazioni):
            if p.stato == StatoPrenotazione.ATTIVA and p.lezione.inizio > adesso:
                regole._libera_posto(db, p.lezione, p, StatoPrenotazione.DISDETTA, "Account cancellato")
        for a in db.scalars(select(Attesa).where(Attesa.utente_id == utente.id)):
            db.delete(a)
    utente.email = f"cancellata-{utente.id}@invalid.example"
    utente.nome = "Account"
    utente.cognome = "cancellato"
    utente.telefono = ""
    utente.password_hash = None
    utente.sessione += 1
    utente.cancellato_il = adesso
    db.commit()
