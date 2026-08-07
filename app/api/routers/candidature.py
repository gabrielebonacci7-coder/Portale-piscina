"""Candidature agli annunci."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import HTTP_422_DATI_NON_VALIDI, CurrentUser, DbSession
from app.crud import annuncio as crud_annuncio
from app.crud import candidatura as crud
from app.models import Candidatura, StatoCandidatura
from app.schemas.candidatura import (
    CandidaturaConAnnuncio,
    CandidaturaCreate,
    CandidaturaRead,
)
from app.schemas.pagina import Pagina

router = APIRouter(tags=["candidature"])


def _annuncio_o_404(db, annuncio_id: int):
    annuncio = crud_annuncio.get(db, annuncio_id)
    if annuncio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annuncio non trovato")
    return annuncio


def _candidatura_sul_mio_annuncio(db, annuncio_id: int, candidatura_id: int, utente) -> Candidatura:
    """Recupera la candidatura verificando che l'annuncio sia di chi chiama."""
    annuncio = _annuncio_o_404(db, annuncio_id)
    if annuncio.autore_id != utente.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Puoi gestire solo le candidature ai tuoi annunci"
        )
    candidatura = crud.get(db, candidatura_id)
    if candidatura is None or candidatura.annuncio_id != annuncio.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidatura non trovata")
    return candidatura


@router.post(
    "/annunci/{annuncio_id}/candidature",
    response_model=CandidaturaRead,
    status_code=status.HTTP_201_CREATED,
)
def candidati(annuncio_id: int, dati: CandidaturaCreate, utente: CurrentUser, db: DbSession):
    """Proponiti per un turno pubblicato da qualcun altro."""
    annuncio = _annuncio_o_404(db, annuncio_id)

    if annuncio.autore_id == utente.id:
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, "Non puoi candidarti a un tuo annuncio")
    if utente.profilo is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Completa prima il tuo profilo, poi potrai candidarti"
        )
    if not crud.tipo_candidato_corretto(annuncio, utente):
        raise HTTPException(
            HTTP_422_DATI_NON_VALIDI,
            f"A un annuncio '{annuncio.tipo.value}' non può rispondere un account "
            f"'{utente.tipo.value}'",
        )
    if not crud.annuncio_aperto(annuncio):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "L'annuncio non accetta più candidature"
        )
    if not crud.brevetto_sufficiente(annuncio, utente):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Serve un brevetto valido di livello {annuncio.brevetto_richiesto.value} o superiore",
        )

    esistente = crud.gia_candidato(db, annuncio.id, utente.id)
    if esistente is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ti sei già candidato a questo annuncio (stato: {esistente.stato.value})",
        )

    return crud.crea(db, annuncio, utente, dati)


@router.get("/annunci/{annuncio_id}/candidature", response_model=Pagina[CandidaturaRead])
def elenco_candidature(
    annuncio_id: int,
    utente: CurrentUser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Chi si è candidato. Visibile solo a chi ha pubblicato l'annuncio."""
    annuncio = _annuncio_o_404(db, annuncio_id)
    if annuncio.autore_id != utente.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Le candidature sono visibili solo a chi ha pubblicato"
        )
    totale, elementi = crud.per_annuncio(db, annuncio_id, skip=skip, limit=limit)
    return Pagina(totale=totale, skip=skip, limit=limit, elementi=elementi)


@router.post(
    "/annunci/{annuncio_id}/candidature/{candidatura_id}/accetta", response_model=CandidaturaRead
)
def accetta(annuncio_id: int, candidatura_id: int, utente: CurrentUser, db: DbSession):
    """Accetta: assegna il turno e rifiuta le altre candidature in attesa."""
    candidatura = _candidatura_sul_mio_annuncio(db, annuncio_id, candidatura_id, utente)
    if candidatura.stato != StatoCandidatura.INVIATA:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"La candidatura è già '{candidatura.stato.value}'"
        )
    if not crud.annuncio_aperto(candidatura.annuncio):
        raise HTTPException(status.HTTP_409_CONFLICT, "L'annuncio non è più aperto")
    return crud.accetta(db, candidatura)


@router.post(
    "/annunci/{annuncio_id}/candidature/{candidatura_id}/rifiuta", response_model=CandidaturaRead
)
def rifiuta(annuncio_id: int, candidatura_id: int, utente: CurrentUser, db: DbSession):
    candidatura = _candidatura_sul_mio_annuncio(db, annuncio_id, candidatura_id, utente)
    if candidatura.stato != StatoCandidatura.INVIATA:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"La candidatura è già '{candidatura.stato.value}'"
        )
    return crud.rifiuta(db, candidatura)


@router.get("/candidature/mie", response_model=Pagina[CandidaturaConAnnuncio])
def mie_candidature(
    utente: CurrentUser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Le proprie candidature, con il titolo e la data del turno."""
    totale, elementi = crud.per_candidato(db, utente.id, skip=skip, limit=limit)
    letti = []
    for c in elementi:
        letta = CandidaturaConAnnuncio.model_validate(c)
        letta.annuncio_titolo = c.annuncio.titolo
        letta.annuncio_data_inizio = c.annuncio.data_inizio
        letti.append(letta)
    return Pagina(totale=totale, skip=skip, limit=limit, elementi=letti)


@router.delete("/candidature/{candidatura_id}", response_model=CandidaturaRead)
def ritira(candidatura_id: int, utente: CurrentUser, db: DbSession):
    """Ritira la propria candidatura, finché è ancora in attesa."""
    candidatura = crud.get(db, candidatura_id)
    if candidatura is None or candidatura.candidato_id != utente.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidatura non trovata")
    if not candidatura.modificabile:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Non puoi ritirare una candidatura '{candidatura.stato.value}'",
        )
    return crud.ritira(db, candidatura)
