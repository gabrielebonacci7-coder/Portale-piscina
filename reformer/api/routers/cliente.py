"""La cliente: calendario, prenotazioni, le sue lezioni, notifiche, profilo."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from reformer.api.deps import regole, utente_corrente
from reformer.db.session import get_db
from reformer.dominio import orario
from reformer.models import Avviso, Movimento, Notifica, Utente
from reformer.servizi import account, viste
from reformer.servizi import regole as r

router = APIRouter(prefix="/api", tags=["cliente"])


# ----------------------------------------------------------------- lezioni
@router.get("/lezioni")
def calendario(
    da: date | None = None,
    giorni: int = Query(default=31, ge=1, le=62),
    utente: Utente = Depends(utente_corrente),
    db: Session = Depends(get_db),
) -> list[dict]:
    lezioni = r.lezioni_nel_periodo(db, da or orario.oggi(), giorni)
    return [viste.per_cliente(lez, utente) for lez in lezioni]


@router.post("/lezioni/{lezione_id}/prenota")
def prenota(lezione_id: int, utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> dict:
    with regole():
        r.prenota(db, lezione_id, utente)
    db.refresh(utente)
    return {"lezione": viste.per_cliente(r.trova_lezione(db, lezione_id), utente), "utente": viste.utente(utente)}


@router.delete("/lezioni/{lezione_id}/prenota")
def disdici(lezione_id: int, utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> dict:
    with regole():
        r.disdici(db, lezione_id, utente)
    db.refresh(utente)
    return {"lezione": viste.per_cliente(r.trova_lezione(db, lezione_id), utente), "utente": viste.utente(utente)}


@router.post("/lezioni/{lezione_id}/attesa")
def attesa(lezione_id: int, utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> dict:
    with regole():
        posizione = r.entra_in_attesa(db, lezione_id, utente)
    return {"posizione": posizione, "lezione": viste.per_cliente(r.trova_lezione(db, lezione_id), utente)}


@router.delete("/lezioni/{lezione_id}/attesa", status_code=204)
def esci_attesa(lezione_id: int, utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> None:
    with regole():
        r.esci_dall_attesa(db, lezione_id, utente)


@router.get("/mie")
def mie(utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> dict:
    """In programma, in attesa, già fatte (le ultime 20)."""
    from reformer.models import Attesa, Lezione, Prenotazione, StatoPrenotazione

    adesso = orario.adesso()
    prenotate = db.scalars(
        select(Lezione).join(Prenotazione).where(
            Prenotazione.utente_id == utente.id, Prenotazione.stato == StatoPrenotazione.ATTIVA
        ).order_by(Lezione.inizio)
    ).unique().all()
    in_attesa = db.scalars(
        select(Lezione).join(Attesa).where(Attesa.utente_id == utente.id, Lezione.inizio > adesso)
        .order_by(Lezione.inizio)
    ).unique().all()
    prossime = [l for l in prenotate if r.fine_lezione(l) > adesso and not l.annullata_il]
    fatte = [l for l in prenotate if r.fine_lezione(l) <= adesso][::-1][:20]
    return {
        "prossime": [viste.per_cliente(l, utente) for l in prossime],
        "attesa": [viste.per_cliente(l, utente) for l in in_attesa if not l.annullata_il],
        "fatte": [viste.per_cliente(l, utente) for l in fatte],
    }


# --------------------------------------------------------------- pacchetto
@router.get("/pacchetto")
def pacchetto(utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> dict:
    movimenti = db.scalars(
        select(Movimento).where(Movimento.utente_id == utente.id)
        .order_by(Movimento.creato_il.desc(), Movimento.id.desc()).limit(30)
    ).all()
    return {
        "lezioni_rimaste": utente.lezioni_rimaste,
        "scadenza": utente.scadenza.isoformat() if utente.scadenza else None,
        "movimenti": [
            {"quando": m.creato_il.isoformat(), "variazione": m.variazione, "saldo": m.saldo, "motivo": m.motivo}
            for m in movimenti
        ],
    }


# --------------------------------------------------------------- notifiche
@router.get("/notifiche")
def notifiche(utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> dict:
    personali = db.scalars(
        select(Notifica).where(Notifica.utente_id == utente.id).order_by(Notifica.creato_il.desc()).limit(40)
    ).all()
    avvisi = db.scalars(select(Avviso).order_by(Avviso.creato_il.desc()).limit(20)).all()
    visti = utente.avvisi_visti_il
    elenco = [
        {"tipo": "personale", "testo": n.testo, "quando": n.creato_il.isoformat(), "letta": n.letta_il is not None}
        for n in personali
    ] + [
        {
            "tipo": "avviso", "testo": a.testo, "quando": a.creato_il.isoformat(),
            "da": a.autore.nome if a.autore else "Lo studio",
            "letta": visti is not None and a.creato_il <= visti,
        }
        for a in avvisi
    ]
    elenco.sort(key=lambda x: x["quando"], reverse=True)
    return {"elenco": elenco, "non_lette": sum(1 for x in elenco if not x["letta"])}


@router.post("/notifiche/lette", status_code=204)
def segna_lette(utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> None:
    adesso = datetime.now(timezone.utc)
    for n in db.scalars(select(Notifica).where(Notifica.utente_id == utente.id, Notifica.letta_il.is_(None))):
        n.letta_il = adesso
    utente.avvisi_visti_il = adesso
    db.commit()


# ------------------------------------------------------------------ profilo
class Profilo(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    cognome: str = Field(min_length=1, max_length=80)
    telefono: str = Field(min_length=6, max_length=30)


class CambioPassword(BaseModel):
    attuale: str = Field(max_length=200)
    nuova: str = Field(min_length=8, max_length=72)


class ConPassword(BaseModel):
    password: str = Field(max_length=200)


@router.get("/io")
def io(utente: Utente = Depends(utente_corrente)) -> dict:
    return viste.utente(utente)


@router.patch("/io")
def modifica_io(dati: Profilo, utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> dict:
    utente.nome, utente.cognome, utente.telefono = dati.nome.strip(), dati.cognome.strip(), dati.telefono.strip()
    db.commit()
    return viste.utente(utente)


@router.post("/io/password")
def cambia_password(
    dati: CambioPassword, utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)
) -> dict:
    from reformer.core.security import crea_token

    with regole():
        account.cambia_password(db, utente, dati.attuale, dati.nuova)
    # Gli altri telefoni escono; questo riceve un token nuovo e resta dentro.
    return {"token": crea_token(utente.id, utente.sessione)}


@router.get("/io/esporta")
def esporta(utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> dict:
    return account.esporta(db, utente)


@router.post("/io/cancella", status_code=204)
def cancella(dati: ConPassword, utente: Utente = Depends(utente_corrente), db: Session = Depends(get_db)) -> None:
    with regole():
        account.cancella(db, utente, dati.password)
