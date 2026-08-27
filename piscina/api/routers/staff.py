"""Il gestionale: chi ha prenotato, con nome, telefono ed email.

È l'unica parte dell'app che mostra dati personali, e sta dietro a un accesso
con password. Gli account li crea la direzione da riga di comando: non c'è
nessuna registrazione da nessuna parte.
"""

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from piscina.api.deps import operatore_corrente
from piscina.core.config import settings
from piscina.core.limiti import azzera, controlla, ip_richiedente
from piscina.core.security import crea_token, verifica_password
from piscina.crud import prenotazioni as crud
from piscina.db.session import get_db
from piscina.dominio import listino
from piscina.dominio.disponibilita import ETICHETTE, orario_esteso
from piscina.dominio.orologio import oggi
from piscina.models import ANNULLATA, STATI, Operatore, Postazione, Prenotazione
from piscina.schemas import AccessoIn, CambioStatoIn, PostazioneStaffIn, TokenOut

router = APIRouter(prefix="/api/staff", tags=["staff"])


@router.post("/accesso", response_model=TokenOut)
def accesso(dati: AccessoIn, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    email = str(dati.email).lower()
    chiave = f"accesso:{ip_richiedente(request)}"
    controlla(chiave, settings.max_accessi_staff, "Troppi tentativi. Riprova fra un'ora.")

    operatore = db.scalar(select(Operatore).where(Operatore.email == email))
    # Stessa risposta per email sconosciuta e password sbagliata: dire quale
    # delle due è servirebbe solo a chi sta provando a indovinare.
    if operatore is None or not operatore.attivo or not verifica_password(
        dati.password, operatore.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o password non validi"
        )

    azzera(chiave)
    return TokenOut(token=crea_token(operatore.id), nome=operatore.nome, email=operatore.email)


@router.get("/io")
def chi_sono(operatore: Operatore = Depends(operatore_corrente)) -> dict:
    return {"nome": operatore.nome, "email": operatore.email}


def _riga_gestionale(p: Prenotazione) -> dict:
    return {
        "codice": p.codice,
        "giorno": p.giorno.isoformat(),
        "fascia": p.fascia,
        "fascia_etichetta": ETICHETTE[p.fascia],
        "orario": orario_esteso(p.fascia),
        "nome": p.nome,
        "telefono": p.telefono,
        "email": p.email,
        "persone": p.persone,
        "note": p.note,
        "stato": p.stato,
        "postazioni": p.codici_postazioni,
        "lettini": sum(r.lettini for r in p.righe),
        "totale_cent": p.totale_cent,
        "totale": listino.euro(p.totale_cent),
        "creato_il": p.creato_il.isoformat(),
    }


def _elenco(db: Session, giorno: date, cerca: str = "") -> list[Prenotazione]:
    prenotazioni = crud.del_giorno(db, giorno)
    if cerca:
        aghi = cerca.strip().lower()
        cifre = "".join(c for c in aghi if c.isdigit())
        # Meno di tre cifre non è un numero di telefono: è la "2" di "B2", e
        # cercarla nei telefoni troverebbe mezzo registro.
        if len(cifre) < 3:
            cifre = ""
        prenotazioni = [
            p
            for p in prenotazioni
            if aghi in p.nome.lower()
            or aghi in p.email.lower()
            or aghi in p.codice.lower()
            or (cifre and cifre in "".join(c for c in p.telefono if c.isdigit()))
            or any(aghi.upper() == c for c in p.codici_postazioni)
        ]
    return prenotazioni


@router.get("/prenotazioni")
def elenco_prenotazioni(
    giorno: date | None = Query(default=None),
    cerca: str = Query(default=""),
    db: Session = Depends(get_db),
    operatore: Operatore = Depends(operatore_corrente),
) -> dict:
    """Le prenotazioni di un giorno, con i contatti di chi le ha fatte."""
    giorno = giorno or oggi()
    prenotazioni = _elenco(db, giorno, cerca)
    attive = [p for p in prenotazioni if p.stato != ANNULLATA]

    return {
        "giorno": giorno.isoformat(),
        "prenotazioni": [_riga_gestionale(p) for p in prenotazioni],
        "riepilogo": {
            "prenotazioni": len(attive),
            "persone": sum(p.persone for p in attive),
            "ombrelloni": sum(
                1 for p in attive for r in p.righe if r.postazione.tipo == "ombrellone"
            ),
            "lettini": sum(
                r.lettini + (1 if r.postazione.tipo == "lettino" else 0)
                for p in attive
                for r in p.righe
            ),
            "annullate": len(prenotazioni) - len(attive),
            "incasso_previsto_cent": sum(p.totale_cent for p in attive),
            "incasso_previsto": listino.euro(sum(p.totale_cent for p in attive)),
        },
    }


@router.get("/prenotazioni.csv")
def esporta_csv(
    giorno: date | None = Query(default=None),
    db: Session = Depends(get_db),
    operatore: Operatore = Depends(operatore_corrente),
) -> StreamingResponse:
    """Il giorno in un foglio di calcolo, per chi tiene i conti a parte."""
    giorno = giorno or oggi()
    buffer = io.StringIO()
    # `;` e BOM: è così che Excel in italiano apre un CSV senza incolonnare
    # tutto in una colonna sola e senza mangiarsi gli accenti.
    buffer.write("﻿")
    scrittore = csv.writer(buffer, delimiter=";")
    scrittore.writerow(
        ["Codice", "Giorno", "Fascia", "Postazioni", "Lettini", "Persone",
         "Nome", "Telefono", "Email", "Stato", "Totale noleggio", "Note"]
    )
    for p in crud.del_giorno(db, giorno):
        scrittore.writerow(
            [
                p.codice,
                p.giorno.strftime("%d/%m/%Y"),
                ETICHETTE[p.fascia],
                " ".join(p.codici_postazioni),
                sum(r.lettini for r in p.righe),
                p.persone,
                p.nome,
                p.telefono,
                p.email,
                p.stato,
                listino.euro(p.totale_cent),
                p.note,
            ]
        )
    buffer.seek(0)
    nome_file = f"prenotazioni-{giorno:%Y-%m-%d}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nome_file}"'},
    )


@router.patch("/prenotazioni/{codice}")
def cambia_stato(
    codice: str,
    dati: CambioStatoIn,
    db: Session = Depends(get_db),
    operatore: Operatore = Depends(operatore_corrente),
) -> dict:
    """Segna arrivato, rimetti in attesa, annulla."""
    if dati.stato not in STATI:
        raise HTTPException(status_code=400, detail=f"stato sconosciuto: {dati.stato}")
    prenotazione = crud.per_codice(db, codice)
    if prenotazione is None:
        raise HTTPException(status_code=404, detail="Prenotazione non trovata")
    crud.cambia_stato(db, prenotazione, dati.stato)
    return _riga_gestionale(prenotazione)


@router.get("/postazioni")
def elenco_postazioni(
    db: Session = Depends(get_db),
    operatore: Operatore = Depends(operatore_corrente),
) -> list[dict]:
    return [
        {"codice": p.codice, "tipo": p.tipo, "attiva": p.attiva, "nota": p.nota}
        for p in db.scalars(select(Postazione).order_by(Postazione.codice))
    ]


@router.patch("/postazioni/{codice}")
def modifica_postazione(
    codice: str,
    dati: PostazioneStaffIn,
    db: Session = Depends(get_db),
    operatore: Operatore = Depends(operatore_corrente),
) -> dict:
    """Spegne o riaccende una postazione: ombrellone rotto, zona chiusa.

    Spegnerla non cancella le prenotazioni già prese: quelle restano, e chi le
    ha fatte va avvisato a voce. Impedisce solo che ne arrivino di nuove.
    """
    postazione = db.scalar(select(Postazione).where(Postazione.codice == codice.upper()))
    if postazione is None:
        raise HTTPException(status_code=404, detail="Postazione non trovata")
    if dati.attiva is not None:
        postazione.attiva = dati.attiva
    if dati.nota is not None:
        postazione.nota = dati.nota.strip()
    db.commit()
    db.refresh(postazione)
    return {
        "codice": postazione.codice,
        "attiva": postazione.attiva,
        "nota": postazione.nota,
    }
