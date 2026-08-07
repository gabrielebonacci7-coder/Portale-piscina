"""Caricamento delle foto: profilo del bagnino e galleria della struttura."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.api.deps import (
    HTTP_413_FILE_TROPPO_GRANDE,
    HTTP_422_DATI_NON_VALIDI,
    CurrentBagnino,
    CurrentPiscina,
    DbSession,
)
from app.core.config import settings
from app.core.immagini import ErroreImmagine
from app.crud import foto as crud
from app.models import TipoFoto
from app.schemas.bagnino import ProfiloBagninoRead
from app.schemas.piscina import FotoRead

router = APIRouter(tags=["foto"])


async def _leggi(file: UploadFile) -> bytes:
    """Legge il file rifiutandolo se supera il limite, senza tenerlo tutto in RAM.

    Ci si fida della dimensione reale, non di `content-length` né del tipo
    dichiarato dal browser: entrambi si falsificano in un attimo.
    """
    pezzi = []
    letti = 0
    while pezzo := await file.read(64 * 1024):
        letti += len(pezzo)
        if letti > settings.max_upload_bytes:
            limite = settings.max_upload_bytes // (1024 * 1024)
            raise HTTPException(
                HTTP_413_FILE_TROPPO_GRANDE,
                f"La foto supera {limite} MB. Provane una più leggera.",
            )
        pezzi.append(pezzo)
    return b"".join(pezzi)


# --- Foto profilo del bagnino ---------------------------------------------
@router.put("/bagnini/me/foto", response_model=ProfiloBagninoRead)
async def carica_foto_bagnino(
    profilo: CurrentBagnino, db: DbSession, file: Annotated[UploadFile, File()]
):
    """Carica o sostituisce la foto profilo."""
    dati = await _leggi(file)
    try:
        return crud.imposta_foto_bagnino(db, profilo, dati)
    except ErroreImmagine as e:
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, str(e))


@router.delete("/bagnini/me/foto", response_model=ProfiloBagninoRead)
def rimuovi_foto_bagnino(profilo: CurrentBagnino, db: DbSession):
    return crud.rimuovi_foto_bagnino(db, profilo)


# --- Galleria della struttura ---------------------------------------------
@router.post(
    "/piscine/me/foto", response_model=FotoRead, status_code=status.HTTP_201_CREATED
)
async def aggiungi_foto_piscina(
    piscina: CurrentPiscina,
    db: DbSession,
    file: Annotated[UploadFile, File()],
    tipo: Annotated[TipoFoto, Form()] = TipoFoto.ALTRO,
    didascalia: Annotated[str | None, Form()] = None,
):
    """Aggiunge una foto alla struttura.

    Dell'ingresso se ne tiene una sola: caricandone un'altra si sostituisce
    quella vecchia, perché è il riferimento per trovare il posto e averne due
    diverse confonderebbe.
    """
    if len(piscina.foto) >= settings.max_foto_piscina:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Hai già {settings.max_foto_piscina} foto: eliminane una per aggiungerne un'altra.",
        )

    dati = await _leggi(file)

    if tipo == TipoFoto.INGRESSO and piscina.foto_ingresso is not None:
        crud.elimina_foto_piscina(db, piscina, piscina.foto_ingresso.id)

    try:
        return crud.aggiungi_foto_piscina(
            db, piscina, dati, tipo, (didascalia or "").strip() or None
        )
    except ErroreImmagine as e:
        raise HTTPException(HTTP_422_DATI_NON_VALIDI, str(e))


@router.delete("/piscine/me/foto/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def elimina_foto_piscina(foto_id: int, piscina: CurrentPiscina, db: DbSession):
    if not crud.elimina_foto_piscina(db, piscina, foto_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foto non trovata")
