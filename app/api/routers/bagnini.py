"""Profili bagnino: creazione, modifica, ricerca, brevetti/esperienze/disponibilità."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentBagnino, CurrentUser, DbSession, richiede_login
from app.crud import bagnino as crud
from app.models import Brevetto, Disponibilita, Esperienza, TipoUtente
from app.schemas.bagnino import (
    BrevettoCreate,
    BrevettoRead,
    DisponibilitaCreate,
    DisponibilitaRead,
    EsperienzaCreate,
    EsperienzaRead,
    ProfiloBagninoCreate,
    ProfiloBagninoRead,
    ProfiloBagninoSintesi,
    ProfiloBagninoUpdate,
)
from app.schemas.pagina import Pagina

router = APIRouter(prefix="/bagnini", tags=["bagnini"])


@router.post("", response_model=ProfiloBagninoRead, status_code=status.HTTP_201_CREATED)
def crea_profilo(dati: ProfiloBagninoCreate, utente: CurrentUser, db: DbSession):
    """Crea il profilo del bagnino collegato all'account autenticato."""
    if utente.tipo != TipoUtente.BAGNINO:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Riservato agli account bagnino")
    if utente.profilo_bagnino is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Profilo già creato: usa PATCH /bagnini/me")
    return crud.crea(db, utente.id, dati)


@router.get("", response_model=Pagina[ProfiloBagninoSintesi], dependencies=[richiede_login])
def cerca_bagnini(
    db: DbSession,
    citta: str | None = None,
    zona_id: int | None = None,
    solo_abilitati: bool = Query(False, description="Solo chi ha un brevetto non scaduto"),
    chiamata_singola: bool | None = Query(None, description="Disponibile per turni spot"),
    anni_esperienza_min: int | None = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Elenco dei bagnini che cercano lavoro, con filtri."""
    totale, elementi = crud.cerca(
        db,
        citta=citta,
        zona_id=zona_id,
        solo_abilitati=solo_abilitati,
        chiamata_singola=chiamata_singola,
        anni_esperienza_min=anni_esperienza_min,
        skip=skip,
        limit=limit,
    )
    return Pagina(totale=totale, skip=skip, limit=limit, elementi=elementi)


@router.get("/me", response_model=ProfiloBagninoRead)
def mio_profilo(profilo: CurrentBagnino):
    return profilo


@router.patch("/me", response_model=ProfiloBagninoRead)
def aggiorna_profilo(dati: ProfiloBagninoUpdate, profilo: CurrentBagnino, db: DbSession):
    return crud.aggiorna(db, profilo, dati)


@router.get("/{bagnino_id}", response_model=ProfiloBagninoRead, dependencies=[richiede_login])
def dettaglio_bagnino(bagnino_id: int, db: DbSession):
    profilo = crud.get(db, bagnino_id)
    if profilo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bagnino non trovato")
    return profilo


# --- Brevetti -------------------------------------------------------------
@router.post("/me/brevetti", response_model=BrevettoRead, status_code=status.HTTP_201_CREATED)
def aggiungi_brevetto(dati: BrevettoCreate, profilo: CurrentBagnino, db: DbSession):
    return crud.aggiungi_brevetto(db, profilo, dati)


@router.delete("/me/brevetti/{brevetto_id}", status_code=status.HTTP_204_NO_CONTENT)
def elimina_brevetto(brevetto_id: int, profilo: CurrentBagnino, db: DbSession):
    if not crud.elimina_figlio(db, Brevetto, brevetto_id, profilo):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brevetto non trovato")


# --- Esperienze -----------------------------------------------------------
@router.post("/me/esperienze", response_model=EsperienzaRead, status_code=status.HTTP_201_CREATED)
def aggiungi_esperienza(dati: EsperienzaCreate, profilo: CurrentBagnino, db: DbSession):
    return crud.aggiungi_esperienza(db, profilo, dati)


@router.delete("/me/esperienze/{esperienza_id}", status_code=status.HTTP_204_NO_CONTENT)
def elimina_esperienza(esperienza_id: int, profilo: CurrentBagnino, db: DbSession):
    if not crud.elimina_figlio(db, Esperienza, esperienza_id, profilo):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esperienza non trovata")


# --- Disponibilità --------------------------------------------------------
@router.post(
    "/me/disponibilita", response_model=DisponibilitaRead, status_code=status.HTTP_201_CREATED
)
def aggiungi_disponibilita(dati: DisponibilitaCreate, profilo: CurrentBagnino, db: DbSession):
    return crud.aggiungi_disponibilita(db, profilo, dati)


@router.delete("/me/disponibilita/{disponibilita_id}", status_code=status.HTTP_204_NO_CONTENT)
def elimina_disponibilita(disponibilita_id: int, profilo: CurrentBagnino, db: DbSession):
    if not crud.elimina_figlio(db, Disponibilita, disponibilita_id, profilo):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disponibilità non trovata")
