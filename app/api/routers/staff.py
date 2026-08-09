"""Pannello di gestione: verifica documenti, sospensione account, registro.

Tutte le rotte sono sotto `/staff` e passano da `CurrentStaff`. A chi non è
staff rispondono 404: il pannello non deve nemmeno risultare esistente.
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, DbSession, HTTP_422_DATI_NON_VALIDI
from app.crud import staff as crud
from app.models import Brevetto, TipoUtente, Utente
from app.schemas.pagina import Pagina
from app.schemas.staff import (
    AzioneStaffRead,
    BrevettoStaff,
    Riepilogo,
    SospensioneRequest,
    UtenteStaff,
    VerificaRequest,
)

router = APIRouter(prefix="/staff", tags=["staff"])


def _scheda(utente: Utente) -> UtenteStaff:
    """Riga dell'elenco account, con i numeri dei brevetti se è un bagnino."""
    scheda = UtenteStaff.model_validate(utente)
    scheda.nome = utente.nome_visualizzato if utente.profilo else None
    if utente.profilo_bagnino:
        brevetti = utente.profilo_bagnino.brevetti
        scheda.brevetti = len(brevetti)
        scheda.brevetti_da_verificare = sum(1 for b in brevetti if not b.verificato)
    return scheda


def _brevetto(brevetto: Brevetto) -> BrevettoStaff:
    bagnino = brevetto.bagnino
    return BrevettoStaff(
        id=brevetto.id,
        tipo=brevetto.tipo,
        ente=brevetto.ente,
        numero=brevetto.numero,
        data_rilascio=brevetto.data_rilascio,
        data_scadenza=brevetto.data_scadenza,
        verificato=brevetto.verificato,
        valido=brevetto.valido,
        bagnino_id=bagnino.id,
        utente_id=bagnino.utente_id,
        nome=bagnino.nome_completo,
        email=bagnino.utente.email,
    )


def _bersaglio(db: Session, utente_id: int, staff: Utente) -> Utente:
    """L'account su cui si sta agendo, con i controlli comuni.

    Lo staff non tocca né sé stesso né gli altri membri dello staff: le
    sospensioni fra colleghi si fanno da riga di comando, dove serve accesso
    al server. Evita sia l'autoblocco per sbaglio sia il litigio a colpi di
    pulsante.
    """
    bersaglio = db.get(Utente, utente_id)
    if bersaglio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utente non trovato")
    if bersaglio.id == staff.id:
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, "Non puoi agire sul tuo stesso account")
    if bersaglio.e_staff:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Gli account dello staff si gestiscono da riga di comando",
        )
    return bersaglio


@router.get("/riepilogo", response_model=Riepilogo)
def riepilogo(staff: CurrentStaff, db: DbSession):
    """Quanto lavoro c'è in coda."""
    return Riepilogo(**crud.riepilogo(db))


@router.get("/utenti", response_model=Pagina[UtenteStaff])
def elenco_utenti(
    staff: CurrentStaff,
    db: DbSession,
    q: str | None = Query(None, max_length=100, description="Cerca in email, telefono, nome"),
    tipo: TipoUtente | None = None,
    solo_sospesi: bool = False,
    solo_da_verificare: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
):
    totale, elementi = crud.cerca_utenti(
        db,
        q=q,
        tipo=tipo,
        solo_sospesi=solo_sospesi,
        solo_da_verificare=solo_da_verificare,
        skip=skip,
        limit=limit,
    )
    return Pagina(
        totale=totale, skip=skip, limit=limit, elementi=[_scheda(u) for u in elementi]
    )


@router.get("/brevetti", response_model=Pagina[BrevettoStaff])
def elenco_brevetti(
    staff: CurrentStaff,
    db: DbSession,
    solo_da_verificare: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
):
    """Coda di verifica dei brevetti: i più vecchi in cima."""
    totale, elementi = crud.brevetti(
        db, solo_da_verificare=solo_da_verificare, skip=skip, limit=limit
    )
    return Pagina(
        totale=totale, skip=skip, limit=limit, elementi=[_brevetto(b) for b in elementi]
    )


@router.post("/brevetti/{brevetto_id}/verifica", response_model=BrevettoStaff)
def verifica_brevetto(
    brevetto_id: int, dati: VerificaRequest, staff: CurrentStaff, db: DbSession
):
    """Segna il brevetto come controllato sull'originale (o toglie la spunta)."""
    brevetto = db.get(Brevetto, brevetto_id)
    if brevetto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brevetto non trovato")
    return _brevetto(crud.verifica_brevetto(db, staff, brevetto, dati.valore, dati.motivo))


@router.post("/utenti/{utente_id}/verifica", response_model=UtenteStaff)
def verifica_utente(utente_id: int, dati: VerificaRequest, staff: CurrentStaff, db: DbSession):
    """Spunta "verificato" sull'account: documenti o struttura controllati."""
    bersaglio = _bersaglio(db, utente_id, staff)
    return _scheda(crud.verifica_utente(db, staff, bersaglio, dati.valore, dati.motivo))


@router.post("/utenti/{utente_id}/stato", response_model=UtenteStaff)
def stato_utente(utente_id: int, dati: SospensioneRequest, staff: CurrentStaff, db: DbSession):
    """Sospende o riattiva un account. Il motivo è obbligatorio per sospendere."""
    bersaglio = _bersaglio(db, utente_id, staff)
    if not dati.attivo and not (dati.motivo or "").strip():
        raise HTTPException(
            HTTP_422_DATI_NON_VALIDI, "Indica il motivo della sospensione"
        )
    return _scheda(crud.imposta_stato(db, staff, bersaglio, dati.attivo, dati.motivo))


@router.get("/registro", response_model=Pagina[AzioneStaffRead])
def registro(
    staff: CurrentStaff,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
):
    """Storico di tutte le azioni fatte dallo staff."""
    totale, elementi = crud.registro(db, skip=skip, limit=limit)
    return Pagina(totale=totale, skip=skip, limit=limit, elementi=elementi)
