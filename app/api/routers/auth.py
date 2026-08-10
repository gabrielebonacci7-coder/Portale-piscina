"""Registrazione, login e gestione del proprio account."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession, HTTP_422_DATI_NON_VALIDI
from app.core import email as posta
from app.core import limiti
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.crud import cancellazione as crud_cancellazione
from app.crud import token_email as crud_token
from app.crud import utente as crud_utente
from app.models import TipoToken
from app.schemas.auth import (
    CambioPassword,
    CancellaAccount,
    ConfermaEmail,
    LoginRequest,
    RegistrazioneRequest,
    ReimpostaPassword,
    RichiestaRecupero,
    Token,
)
from app.schemas.utente import UtenteRead

router = APIRouter(prefix="/auth", tags=["autenticazione"])


@router.post("/registrazione", response_model=UtenteRead, status_code=status.HTTP_201_CREATED)
def registrazione(dati: RegistrazioneRequest, request: Request, db: DbSession):
    """Crea un account. Il profilo (bagnino o piscina) si crea subito dopo."""
    limiti.registra_tentativo(
        f"registrazione:{limiti.ip_richiedente(request)}", settings.limite_registrazioni
    )
    if crud_utente.get_by_email(db, dati.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email già registrata")
    utente = crud_utente.crea_utente(db, dati)
    _manda_verifica(db, utente)
    return utente


@router.post("/login", response_model=Token)
def login(dati: LoginRequest, request: Request, db: DbSession):
    """Login in JSON. Restituisce il token da usare come `Bearer`."""
    # Due contatori diversi, perché fermano due attacchi diversi: quello per IP
    # ferma chi prova mille password su un account solo, quello per indirizzo
    # ferma chi prova la stessa password su mille account cambiando IP.
    per_ip = f"login-ip:{limiti.ip_richiedente(request)}"
    per_email = f"login-email:{dati.email.lower().strip()}"
    limiti.registra_tentativo(per_ip, settings.limite_login)
    limiti.registra_tentativo(per_email, settings.limite_login_per_email)

    utente = crud_utente.autentica(db, dati.email, dati.password)
    if utente is None:
        # Messaggio volutamente generico: non si rivela se l'email esiste.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o password non corretti")
    if not utente.attivo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disattivato")

    # Entrato: gli errori di battitura di prima non contano più.
    limiti.azzera(per_ip)
    limiti.azzera(per_email)
    return Token(access_token=create_access_token(utente.id), utente=utente)


@router.post("/token", response_model=Token, include_in_schema=False)
def login_form(db: DbSession, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Stessa cosa in formato form OAuth2: serve al pulsante Authorize di /docs."""
    utente = crud_utente.autentica(db, form.username, form.password)
    if utente is None or not utente.attivo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o password non corretti")
    return Token(access_token=create_access_token(utente.id), utente=utente)


@router.get("/me", response_model=UtenteRead)
def utente_corrente(utente: CurrentUser):
    """Dati dell'account collegato al token."""
    return utente


@router.post("/cambio-password", status_code=status.HTTP_204_NO_CONTENT)
def cambio_password(dati: CambioPassword, utente: CurrentUser, db: DbSession):
    if not verify_password(dati.password_attuale, utente.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password attuale non corretta")
    crud_utente.cambia_password(db, utente, dati.password_nuova)


# --- I tuoi dati: accesso, portabilità, cancellazione ----------------------
@router.get("/esporta")
def esporta_dati(utente: CurrentUser, db: DbSession):
    """Scarica tutto quello che la piattaforma sa di te, in un file JSON.

    Diritto di accesso e portabilità (artt. 15 e 20 GDPR). Si scarica invece di
    mostrarlo a schermo: chi lo chiede di solito vuole tenerselo.
    """
    dati = crud_cancellazione.esporta(db, utente)
    nome_file = f"guardlink-dati-{utente.id}.json"
    return JSONResponse(
        content=dati,
        headers={"Content-Disposition": f'attachment; filename="{nome_file}"'},
    )


@router.get("/cancellazione/riepilogo")
def riepilogo_cancellazione(utente: CurrentUser):
    """Cosa sparisce e cosa resta, da leggere **prima** di cancellare."""
    return crud_cancellazione.riepilogo(utente)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def cancella_account(dati: CancellaAccount, utente: CurrentUser, db: DbSession):
    """Cancella il proprio account. Non si torna indietro.

    Restano — senza più il tuo nome — le recensioni che hai scritto e i turni
    già svolti: sono anche la storia di chi ha lavorato con te, e cancellarli
    toglierebbe a un'altra persona qualcosa che è pure suo.
    """
    if utente.e_staff:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Un account dello staff va prima riportato a utente normale "
            "(scripts/crea_staff.py --togli)",
        )
    if dati.conferma.strip().upper() != "CANCELLA":
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, "Scrivi CANCELLA per confermare")
    if not verify_password(dati.password, utente.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password non corretta")

    crud_cancellazione.cancella(db, utente)


# --- Verifica dell'indirizzo ---------------------------------------------
def _manda_verifica(db, utente) -> None:
    """Genera il codice e prova a spedirlo.

    Se l'email non parte non si fa fallire la registrazione: l'account esiste
    comunque e il link si può richiedere di nuovo. Meglio un account da
    confermare che un'iscrizione persa per un guasto del server di posta.
    """
    codice = crud_token.crea(db, utente, TipoToken.VERIFICA_EMAIL)
    try:
        posta.email_verifica(utente.email, crud_token.link("verifica", codice))
    except posta.ErroreInvio:
        pass


@router.post("/verifica-email", response_model=UtenteRead)
def verifica_email(dati: ConfermaEmail, db: DbSession):
    """Conferma l'indirizzo con il codice arrivato per email."""
    token = crud_token.trova_valido(db, dati.codice, TipoToken.VERIFICA_EMAIL)
    if token is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Link non valido o scaduto. Chiedine uno nuovo dal tuo profilo.",
        )
    return crud_token.verifica_email(db, token)


@router.post("/invia-verifica", status_code=status.HTTP_204_NO_CONTENT)
def invia_verifica(utente: CurrentUser, db: DbSession):
    """Rimanda il link di conferma a chi è già dentro."""
    if utente.email_verificata:
        raise HTTPException(status.HTTP_409_CONFLICT, "Il tuo indirizzo è già confermato")
    _manda_verifica(db, utente)


# --- Recupero della password ----------------------------------------------
@router.post("/recupero-password", status_code=status.HTTP_204_NO_CONTENT)
def recupero_password(dati: RichiestaRecupero, request: Request, db: DbSession):
    """Manda il link per reimpostare la password.

    Risponde sempre 204, anche se l'indirizzo non è registrato: dire "questa
    email non esiste" permetterebbe a chiunque di scoprire chi è iscritto.
    """
    # Il limite qui non protegge un account: evita che qualcuno usi Guardlink
    # per riempire di email la casella di un'altra persona.
    limiti.registra_tentativo(
        f"recupero:{limiti.ip_richiedente(request)}", settings.limite_recuperi
    )
    utente = crud_utente.get_by_email(db, dati.email)
    if utente is None or not utente.attivo:
        return

    codice = crud_token.crea(db, utente, TipoToken.RECUPERO_PASSWORD)
    try:
        posta.email_recupero(utente.email, crud_token.link("recupero", codice))
    except posta.ErroreInvio:
        # Nemmeno qui si dice niente a chi ha chiesto: il messaggio d'errore
        # rivelerebbe che l'indirizzo esiste.
        pass


@router.post("/reimposta-password", response_model=Token)
def reimposta_password(dati: ReimpostaPassword, db: DbSession):
    """Imposta la nuova password e fa entrare subito."""
    token = crud_token.trova_valido(db, dati.codice, TipoToken.RECUPERO_PASSWORD)
    if token is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Link non valido, già usato o scaduto. Richiedine uno nuovo.",
        )
    utente = crud_token.reimposta_password(db, token, dati.password_nuova)
    return Token(access_token=create_access_token(utente.id), utente=utente)
