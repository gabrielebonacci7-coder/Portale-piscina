"""Quello che vede chi apre l'app: mappa, listino, informazioni."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from piscina.core.config import settings
from piscina.crud import prenotazioni as crud
from piscina.db.session import get_db
from piscina.dominio import listino, piantina, struttura
from piscina.dominio.disponibilita import ETICHETTE, FASCE, orario_esteso
from piscina.dominio.orologio import oggi
from piscina.schemas import MappaOut

router = APIRouter(prefix="/api", tags=["pubblico"])


@router.get("/mappa", response_model=MappaOut)
def mappa(
    giorno: date | None = Query(default=None, description="Predefinito: oggi"),
    db: Session = Depends(get_db),
) -> MappaOut:
    """La vista dall'alto di un giorno, con lo stato di ogni postazione."""
    giorno = giorno or oggi()
    postazioni = crud.mappa_del_giorno(db, giorno)

    libere = sum(1 for p in postazioni if p["libera_mattina"] and p["libera_pomeriggio"])
    mezze = sum(
        1
        for p in postazioni
        if p["attiva"] and (p["libera_mattina"] != p["libera_pomeriggio"])
    )
    occupate = sum(
        1 for p in postazioni
        if p["attiva"] and not p["libera_mattina"] and not p["libera_pomeriggio"]
    )

    return MappaOut(
        giorno=giorno,
        viewbox=piantina.VIEWBOX,
        lettini_disegnati=piantina.LETTINI_DISEGNATI,
        postazioni=postazioni,
        scenografia=piantina.SCENOGRAFIA,
        rotazioni=piantina.ROTAZIONI,
        riepilogo={
            "libere": libere,
            "mezze": mezze,
            "occupate": occupate,
            "spente": sum(1 for p in postazioni if not p["attiva"]),
            "totale": len(postazioni),
        },
    )


@router.get("/listino")
def listino_prezzi() -> dict:
    """Il listino della stagione, così com'è esposto in piscina."""
    return {
        "stagione": struttura.STAGIONE,
        "ingressi": listino.INGRESSI,
        "abbonamenti": listino.ABBONAMENTI,
        "noleggio": listino.NOLEGGIO,
        "note": listino.NOTE_LISTINO,
    }


@router.get("/info")
def info() -> dict:
    """Dati della struttura, orari, fasce e legenda dei colori."""
    return {
        **struttura.scheda(),
        "fasce": [
            {"valore": f, "etichetta": ETICHETTE[f], "orario": orario_esteso(f)}
            for f in FASCE
        ],
        "postazioni": piantina.conta(),
        "giorni_prenotabili": settings.giorni_prenotabili,
        "max_postazioni": settings.max_postazioni_per_prenotazione,
        "primo_giorno": oggi().isoformat(),
        "ultimo_giorno": (oggi() + timedelta(days=settings.giorni_prenotabili)).isoformat(),
    }
