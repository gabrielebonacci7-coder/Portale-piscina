"""Prenotare, ritrovare e annullare: le tre cose che fa un cliente."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from piscina.core import email as posta
from piscina.core.config import settings
from piscina.core.limiti import controlla, ip_richiedente
from piscina.crud import prenotazioni as crud
from piscina.db.session import get_db
from piscina.schemas import AnnullaIn, PrenotazioneIn, PrenotazioneOut

log = logging.getLogger("piscina.prenotazioni")

router = APIRouter(prefix="/api/prenotazioni", tags=["prenotazioni"])

NON_TROVATA = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Nessuna prenotazione con questo codice e questo numero",
)


def _avvisa(prenotazione_id: int) -> None:
    """Le due email, fuori dalla richiesta.

    Girano in sottofondo perché un server SMTP lento non deve far aspettare
    chi ha appena premuto "conferma": il posto è già suo, il database l'ha
    registrato. Se l'invio fallisce resta scritto nel log, e la prenotazione
    si vede comunque nel gestionale.
    """
    from piscina.db.session import SessionLocal

    with SessionLocal() as db:
        prenotazione = db.get(crud.Prenotazione, prenotazione_id)
        if prenotazione is None:
            return
        for invio in (posta.email_staff_nuova_prenotazione, posta.email_cliente_conferma):
            try:
                invio(prenotazione)
            except Exception as e:  # noqa: BLE001 - un'email persa non è un errore per il cliente
                log.error("Email %s fallita per %s: %s", invio.__name__, prenotazione.codice, e)


@router.post("", response_model=PrenotazioneOut, status_code=status.HTTP_201_CREATED)
def prenota(
    dati: PrenotazioneIn,
    request: Request,
    sfondo: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PrenotazioneOut:
    """Registra la prenotazione e avvisa staff e cliente."""
    controlla(
        f"prenota:{ip_richiedente(request)}",
        settings.max_prenotazioni_per_ip,
        "Troppe prenotazioni dallo stesso collegamento. Riprova più tardi "
        "o chiamaci.",
    )

    try:
        prenotazione = crud.crea(
            db,
            giorno=dati.giorno,
            fascia=dati.fascia,
            scelte=[crud.Scelta(codice=p.codice, lettini=p.lettini) for p in dati.postazioni],
            nome=dati.nome,
            telefono=dati.telefono,
            email=str(dati.email),
            persone=dati.persone,
            note=dati.note,
        )
    except crud.RichiestaNonValida as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except crud.PostoOccupato as e:
        # 409: non è colpa di chi chiede, è cambiato il mondo nel frattempo.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    sfondo.add_task(_avvisa, prenotazione.id)
    return PrenotazioneOut.da_modello(prenotazione)


@router.get("/{codice}", response_model=PrenotazioneOut)
def ritrova(
    codice: str,
    telefono: str,
    request: Request,
    db: Session = Depends(get_db),
) -> PrenotazioneOut:
    """La propria prenotazione, con codice e numero di telefono."""
    controlla(
        f"ritrova:{ip_richiedente(request)}",
        settings.max_prenotazioni_per_ip * 3,
        "Troppi tentativi. Riprova fra un po'.",
    )
    prenotazione = crud.per_codice_e_telefono(db, codice, telefono)
    if prenotazione is None:
        raise NON_TROVATA
    return PrenotazioneOut.da_modello(prenotazione)


@router.post("/{codice}/annulla", response_model=PrenotazioneOut)
def annulla(
    codice: str,
    dati: AnnullaIn,
    request: Request,
    sfondo: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PrenotazioneOut:
    """Annulla una prenotazione e libera i posti."""
    controlla(
        f"annulla:{ip_richiedente(request)}",
        settings.max_prenotazioni_per_ip * 3,
        "Troppi tentativi. Riprova fra un po'.",
    )
    prenotazione = crud.per_codice_e_telefono(db, codice, dati.telefono)
    if prenotazione is None:
        raise NON_TROVATA

    crud.annulla(db, prenotazione)
    sfondo.add_task(_annuncia_annullamento, prenotazione.codice)
    return PrenotazioneOut.da_modello(prenotazione)


def _annuncia_annullamento(codice: str) -> None:
    from piscina.db.session import SessionLocal

    with SessionLocal() as db:
        prenotazione = crud.per_codice(db, codice)
        if prenotazione is None:
            return
        for invio in (posta.email_cliente_annullata, posta.email_staff_annullata):
            try:
                invio(prenotazione)
            except Exception as e:  # noqa: BLE001
                log.error("Email di annullamento fallita per %s: %s", codice, e)
