"""Recensioni incrociate fra bagnini e strutture."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, HTTP_422_DATI_NON_VALIDI
from app.crud import annuncio as crud_annuncio
from app.crud import recensione as crud
from app.models import Recensione, Utente
from app.schemas.recensione import RecensioneCreate, RecensioneRead, RiepilogoRecensioni

router = APIRouter(tags=["recensioni"])


def _con_nome_autore(recensione: Recensione) -> RecensioneRead:
    letta = RecensioneRead.model_validate(recensione)
    letta.autore_nome = recensione.autore.nome_visualizzato
    return letta


@router.post(
    "/recensioni", response_model=RecensioneRead, status_code=status.HTTP_201_CREATED
)
def scrivi(dati: RecensioneCreate, utente: CurrentUser, db: DbSession):
    """Recensisce la controparte di un turno concluso insieme."""
    if dati.destinatario_id == utente.id:
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, "Non puoi recensire te stesso")

    destinatario = db.get(Utente, dati.destinatario_id)
    if destinatario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Destinatario non trovato")

    # Si recensisce solo chi si è incontrato davvero su un annuncio.
    if dati.annuncio_id is None:
        raise HTTPException(
            HTTP_422_DATI_NON_VALIDI,
            "Indica l'annuncio a cui si riferisce la recensione",
        )
    annuncio = crud_annuncio.get(db, dati.annuncio_id)
    if annuncio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annuncio non trovato")
    if annuncio.stato not in crud.STATI_RECENSIBILI:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Si può recensire solo dopo che il turno è stato assegnato o chiuso",
        )
    if not crud.hanno_lavorato_insieme(annuncio, utente.id, dati.destinatario_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Non risulta che abbiate lavorato insieme su questo annuncio"
        )

    fuori_posto = crud.voti_fuori_posto(dati, utente)
    if fuori_posto:
        raise HTTPException(
            HTTP_422_DATI_NON_VALIDI,
            f"Voti non validi per un account '{utente.tipo.value}': {', '.join(fuori_posto)}",
        )

    if crud.esiste_gia(db, utente.id, dati.destinatario_id, dati.annuncio_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Hai già recensito questo annuncio")

    return _con_nome_autore(crud.crea(db, utente, dati))


@router.get("/utenti/{utente_id}/recensioni", response_model=RiepilogoRecensioni)
def ricevute(
    utente_id: int,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Recensioni ricevute da un utente, con le medie dei voti."""
    if db.get(Utente, utente_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utente non trovato")

    totale, elementi = crud.elenco_per_destinatario(db, utente_id, skip=skip, limit=limit)
    return RiepilogoRecensioni(
        destinatario_id=utente_id,
        totale=totale,
        recensioni=[_con_nome_autore(r) for r in elementi],
        **crud.medie(db, utente_id),
    )
