"""Chat interna e blocco utenti."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import HTTP_422_DATI_NON_VALIDI, CurrentUser, DbSession
from app.crud import messaggistica as crud
from app.models import Conversazione, Utente
from app.schemas.messaggistica import (
    BloccoCreate,
    BloccoRead,
    ConversazioneAvvia,
    ConversazioneRead,
    MessaggioCreate,
    MessaggioRead,
)
from app.schemas.pagina import Pagina

router = APIRouter(tags=["messaggi"])


def _mia_conversazione(db, conversazione_id: int, utente: Utente) -> Conversazione:
    conversazione = crud.get_conversazione(db, conversazione_id)
    # Chi non partecipa non deve nemmeno sapere che la conversazione esiste.
    if conversazione is None or not crud.partecipa(conversazione, utente.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversazione non trovata")
    return conversazione


def _in_lettura(db, conversazione: Conversazione, utente: Utente) -> ConversazioneRead:
    altro = conversazione.altro_partecipante(utente.id)
    return ConversazioneRead(
        id=conversazione.id,
        annuncio_id=conversazione.annuncio_id,
        interlocutore=altro.utente if altro else None,
        ultimo_messaggio=crud.ultimo_testo(db, conversazione.id),
        ultimo_messaggio_il=conversazione.ultimo_messaggio_il,
        non_letti=crud.conta_non_letti(db, conversazione.id, utente.id),
    )


# --- Conversazioni --------------------------------------------------------
@router.post(
    "/conversazioni", response_model=MessaggioRead, status_code=status.HTTP_201_CREATED
)
def avvia(dati: ConversazioneAvvia, utente: CurrentUser, db: DbSession):
    """Scrive a un altro iscritto. Se la conversazione esiste già, la riusa."""
    if dati.destinatario_id == utente.id:
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, "Non puoi scrivere a te stesso")

    destinatario = db.get(Utente, dati.destinatario_id)
    if destinatario is None or not destinatario.attivo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Destinatario non trovato")
    if utente.profilo is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Completa prima il tuo profilo, poi potrai scrivere"
        )
    if crud.blocco_fra(db, utente.id, destinatario.id) is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Non è possibile scrivere a questo utente")

    conversazione = crud.trova_o_crea_diretta(
        db, utente.id, destinatario.id, annuncio_id=dati.annuncio_id
    )
    return crud.invia(db, conversazione, utente, MessaggioCreate(testo=dati.testo))


@router.get("/conversazioni", response_model=Pagina[ConversazioneRead])
def elenco(
    utente: CurrentUser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
):
    """Le proprie conversazioni, dalla più recente, con i messaggi non letti."""
    totale, conversazioni = crud.elenco_conversazioni(db, utente.id, skip=skip, limit=limit)
    return Pagina(
        totale=totale,
        skip=skip,
        limit=limit,
        elementi=[_in_lettura(db, c, utente) for c in conversazioni],
    )


@router.get("/conversazioni/{conversazione_id}/messaggi", response_model=Pagina[MessaggioRead])
def leggi(
    conversazione_id: int,
    utente: CurrentUser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """I messaggi, dal più vecchio. Aprirli li segna come letti."""
    conversazione = _mia_conversazione(db, conversazione_id, utente)
    totale, elementi = crud.messaggi(db, conversazione.id, skip=skip, limit=limit)
    crud.segna_letta(db, conversazione.id, utente.id)
    return Pagina(totale=totale, skip=skip, limit=limit, elementi=elementi)


@router.post(
    "/conversazioni/{conversazione_id}/messaggi",
    response_model=MessaggioRead,
    status_code=status.HTTP_201_CREATED,
)
def rispondi(
    conversazione_id: int, dati: MessaggioCreate, utente: CurrentUser, db: DbSession
):
    conversazione = _mia_conversazione(db, conversazione_id, utente)
    altro = conversazione.altro_partecipante(utente.id)
    if altro is not None and crud.blocco_fra(db, utente.id, altro.utente_id) is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Non è possibile scrivere a questo utente")
    return crud.invia(db, conversazione, utente, dati)


@router.get("/conversazioni/non-letti", response_model=dict)
def totale_non_letti(utente: CurrentUser, db: DbSession):
    """Contatore complessivo, per il pallino sull'icona dei messaggi."""
    _, conversazioni = crud.elenco_conversazioni(db, utente.id, limit=100)
    totale = sum(crud.conta_non_letti(db, c.id, utente.id) for c in conversazioni)
    return {"non_letti": totale}


# --- Blocchi --------------------------------------------------------------
@router.post(
    "/blocchi/{utente_id}", response_model=BloccoRead, status_code=status.HTTP_201_CREATED
)
def blocca(utente_id: int, dati: BloccoCreate, utente: CurrentUser, db: DbSession):
    """Blocca un utente: da quel momento nessuno dei due può scrivere all'altro."""
    if utente_id == utente.id:
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, "Non puoi bloccare te stesso")
    if db.get(Utente, utente_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utente non trovato")
    return crud.blocca(db, utente, utente_id, dati.motivo)


@router.delete("/blocchi/{utente_id}", status_code=status.HTTP_204_NO_CONTENT)
def sblocca(utente_id: int, utente: CurrentUser, db: DbSession):
    if not crud.sblocca(db, utente.id, utente_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questo utente non è bloccato")


@router.get("/blocchi", response_model=list[BloccoRead])
def elenco_blocchi(utente: CurrentUser, db: DbSession):
    """Chi hai bloccato."""
    return crud.elenco_blocchi(db, utente.id)
