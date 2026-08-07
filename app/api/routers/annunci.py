"""Annunci della bacheca: pubblicazione, ricerca, modifica, assegnazione."""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, HTTP_422_DATI_NON_VALIDI, richiede_login
from app.crud import annuncio as crud
from app.models import Annuncio, StatoAnnuncio, TipoAnnuncio, TipoBrevetto, TipoTurno, Utente
from app.schemas.annuncio import AnnuncioCreate, AnnuncioRead, AnnuncioUpdate
from app.schemas.pagina import Pagina

router = APIRouter(prefix="/annunci", tags=["annunci"])


def _annuncio_di_proprieta(db, annuncio_id: int, utente: Utente) -> Annuncio:
    """Recupera l'annuncio e verifica che chi chiama ne sia l'autore."""
    annuncio = crud.get(db, annuncio_id)
    if annuncio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annuncio non trovato")
    if annuncio.autore_id != utente.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Puoi gestire solo i tuoi annunci")
    return annuncio


@router.post("", response_model=AnnuncioRead, status_code=status.HTTP_201_CREATED)
def pubblica(dati: AnnuncioCreate, utente: CurrentUser, db: DbSession):
    """Pubblica un annuncio. Il tipo deve corrispondere al tipo di account."""
    if utente.profilo is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Completa prima il tuo profilo, poi potrai pubblicare"
        )
    if not crud.tipo_coerente_con_autore(dati.tipo, utente):
        raise HTTPException(
            HTTP_422_DATI_NON_VALIDI,
            f"Un account '{utente.tipo.value}' non può pubblicare un annuncio '{dati.tipo.value}'",
        )
    return crud.crea(db, utente, dati)


@router.get("", response_model=Pagina[AnnuncioRead], dependencies=[richiede_login])
def bacheca(
    db: DbSession,
    tipo: TipoAnnuncio | None = None,
    citta: str | None = None,
    zona_id: int | None = None,
    tipo_turno: TipoTurno | None = None,
    brevetto_richiesto: TipoBrevetto | None = Query(
        None, description="Include anche gli annunci senza brevetto specifico"
    ),
    solo_urgenti: bool = False,
    solo_aperti: bool = Query(True, description="Esclude assegnati, chiusi e turni già passati"),
    data_da: datetime | None = None,
    data_a: datetime | None = None,
    compenso_min: Decimal | None = Query(None, ge=0),
    testo: str | None = Query(None, description="Cerca nel titolo e nelle note"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """La bacheca vera e propria: urgenti in cima, poi i turni più vicini."""
    totale, elementi = crud.cerca(
        db,
        tipo=tipo,
        citta=citta,
        zona_id=zona_id,
        tipo_turno=tipo_turno,
        brevetto_richiesto=brevetto_richiesto,
        solo_urgenti=solo_urgenti,
        solo_aperti=solo_aperti,
        data_da=data_da,
        data_a=data_a,
        compenso_min=compenso_min,
        testo=testo,
        skip=skip,
        limit=limit,
    )
    return Pagina(totale=totale, skip=skip, limit=limit, elementi=elementi)


@router.get("/miei", response_model=Pagina[AnnuncioRead])
def miei_annunci(
    utente: CurrentUser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Tutti i propri annunci, compresi chiusi e scaduti."""
    totale, elementi = crud.cerca(
        db, autore_id=utente.id, solo_aperti=False, skip=skip, limit=limit
    )
    return Pagina(totale=totale, skip=skip, limit=limit, elementi=elementi)


@router.get("/{annuncio_id}", response_model=AnnuncioRead, dependencies=[richiede_login])
def dettaglio(annuncio_id: int, db: DbSession):
    annuncio = crud.get(db, annuncio_id)
    if annuncio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annuncio non trovato")
    return annuncio


@router.patch("/{annuncio_id}", response_model=AnnuncioRead)
def modifica(annuncio_id: int, dati: AnnuncioUpdate, utente: CurrentUser, db: DbSession):
    annuncio = _annuncio_di_proprieta(db, annuncio_id, utente)
    return crud.aggiorna(db, annuncio, dati)


@router.delete("/{annuncio_id}", status_code=status.HTTP_204_NO_CONTENT)
def elimina(annuncio_id: int, utente: CurrentUser, db: DbSession):
    annuncio = _annuncio_di_proprieta(db, annuncio_id, utente)
    crud.elimina(db, annuncio)


@router.post("/{annuncio_id}/assegna", response_model=AnnuncioRead)
def assegna(annuncio_id: int, assegnatario_id: int, utente: CurrentUser, db: DbSession):
    """Assegna il turno a un utente. Solo l'autore dell'annuncio può farlo."""
    annuncio = _annuncio_di_proprieta(db, annuncio_id, utente)
    if annuncio.stato not in (StatoAnnuncio.APERTO, StatoAnnuncio.BOZZA):
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"L'annuncio è già in stato '{annuncio.stato.value}'"
        )

    destinatario = db.get(Utente, assegnatario_id)
    if destinatario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utente da assegnare non trovato")
    if destinatario.id == utente.id:
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, "Non puoi assegnarti il turno")
    if destinatario.tipo == utente.tipo:
        raise HTTPException(
            HTTP_422_DATI_NON_VALIDI,
            "Il turno va assegnato alla controparte, non a un account dello stesso tipo",
        )
    return crud.assegna(db, annuncio, destinatario)


@router.post("/{annuncio_id}/chiudi", response_model=AnnuncioRead)
def chiudi(annuncio_id: int, utente: CurrentUser, db: DbSession):
    """Chiude l'annuncio: il turno è concluso e si possono lasciare recensioni."""
    annuncio = _annuncio_di_proprieta(db, annuncio_id, utente)
    return crud.aggiorna(db, annuncio, AnnuncioUpdate(stato=StatoAnnuncio.CHIUSO))
