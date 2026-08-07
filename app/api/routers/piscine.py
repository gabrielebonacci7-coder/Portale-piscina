"""Profili delle strutture."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentPiscina, CurrentUser, DbSession
from app.crud import piscina as crud
from app.models import TipoStruttura, TipoUtente
from app.schemas.pagina import Pagina
from app.schemas.piscina import ProfiloPiscinaCreate, ProfiloPiscinaRead, ProfiloPiscinaUpdate

router = APIRouter(prefix="/piscine", tags=["piscine"])


@router.post("", response_model=ProfiloPiscinaRead, status_code=status.HTTP_201_CREATED)
def crea_profilo(dati: ProfiloPiscinaCreate, utente: CurrentUser, db: DbSession):
    """Crea il profilo della struttura collegata all'account autenticato."""
    if utente.tipo != TipoUtente.PISCINA:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Riservato agli account piscina")
    if utente.profilo_piscina is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Profilo già creato: usa PATCH /piscine/me")
    return crud.crea(db, utente.id, dati)


@router.get("", response_model=Pagina[ProfiloPiscinaRead])
def cerca_piscine(
    db: DbSession,
    citta: str | None = None,
    zona_id: int | None = None,
    tipo_struttura: TipoStruttura | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    totale, elementi = crud.cerca(
        db,
        citta=citta,
        zona_id=zona_id,
        tipo_struttura=tipo_struttura,
        skip=skip,
        limit=limit,
    )
    return Pagina(totale=totale, skip=skip, limit=limit, elementi=elementi)


@router.get("/me", response_model=ProfiloPiscinaRead)
def mio_profilo(profilo: CurrentPiscina):
    return profilo


@router.patch("/me", response_model=ProfiloPiscinaRead)
def aggiorna_profilo(dati: ProfiloPiscinaUpdate, profilo: CurrentPiscina, db: DbSession):
    return crud.aggiorna(db, profilo, dati)


@router.get("/{piscina_id}", response_model=ProfiloPiscinaRead)
def dettaglio_piscina(piscina_id: int, db: DbSession):
    profilo = crud.get(db, piscina_id)
    if profilo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Struttura non trovata")
    return profilo
