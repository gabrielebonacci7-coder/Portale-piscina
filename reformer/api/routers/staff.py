"""Il gestionale di Greta ed Elisa."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from reformer.api.deps import regole, solo_staff
from reformer.db.session import get_db
from reformer.dominio import orario
from reformer.models import (
    Avviso,
    Lezione,
    Movimento,
    Prenotazione,
    Ruolo,
    StatoPrenotazione,
    Utente,
)
from reformer.servizi import viste
from reformer.servizi import regole as r

router = APIRouter(prefix="/api/staff", tags=["staff"])


# ------------------------------------------------------------------ lezioni
@router.get("/lezioni")
def lezioni(
    da: date | None = None,
    giorni: int = Query(default=7, ge=1, le=62),
    _: Utente = Depends(solo_staff),
    db: Session = Depends(get_db),
) -> list[dict]:
    with regole():
        return [viste.per_staff(l) for l in r.lezioni_nel_periodo(db, da or orario.oggi(), giorni)]


@router.get("/lezioni/{lezione_id}")
def lezione(lezione_id: int, _: Utente = Depends(solo_staff), db: Session = Depends(get_db)) -> dict:
    with regole():
        return viste.per_staff(r.trova_lezione(db, lezione_id))


class Titolo(BaseModel):
    titolo: str = Field(max_length=60)


@router.patch("/lezioni/{lezione_id}")
def cambia_titolo(
    lezione_id: int, dati: Titolo, _: Utente = Depends(solo_staff), db: Session = Depends(get_db)
) -> dict:
    with regole():
        return viste.per_staff(r.cambia_titolo(db, lezione_id, dati.titolo))


class Motivo(BaseModel):
    motivo: str = Field(default="", max_length=200)


@router.post("/lezioni/{lezione_id}/annulla")
def annulla(
    lezione_id: int, dati: Motivo, autore: Utente = Depends(solo_staff), db: Session = Depends(get_db)
) -> dict:
    with regole():
        avvisate = r.annulla_lezione(db, lezione_id, dati.motivo.strip(), autore)
    return {"avvisate": avvisate, "lezione": viste.per_staff(r.trova_lezione(db, lezione_id))}


@router.post("/lezioni/{lezione_id}/ripristina")
def ripristina(lezione_id: int, _: Utente = Depends(solo_staff), db: Session = Depends(get_db)) -> dict:
    with regole():
        r.ripristina_lezione(db, lezione_id)
        return viste.per_staff(r.trova_lezione(db, lezione_id))


class Cliente(BaseModel):
    cliente_id: int


def _cliente(db: Session, cliente_id: int) -> Utente:
    c = db.get(Utente, cliente_id)
    if c is None or c.cancellato_il is not None:
        raise HTTPException(404, "Cliente non trovata")
    return c


@router.post("/lezioni/{lezione_id}/iscritte")
def aggiungi(
    lezione_id: int, dati: Cliente, autore: Utente = Depends(solo_staff), db: Session = Depends(get_db)
) -> dict:
    cliente = _cliente(db, dati.cliente_id)
    with regole():
        r.staff_aggiungi(db, lezione_id, cliente, autore)
        return viste.per_staff(r.trova_lezione(db, lezione_id))


@router.delete("/lezioni/{lezione_id}/iscritte/{cliente_id}")
def togli(
    lezione_id: int, cliente_id: int, autore: Utente = Depends(solo_staff), db: Session = Depends(get_db)
) -> dict:
    with regole():
        entrata = r.staff_togli(db, lezione_id, cliente_id, autore)
        return {
            "entrata": entrata.nome_completo if entrata else None,
            "lezione": viste.per_staff(r.trova_lezione(db, lezione_id)),
        }


class Presenza(BaseModel):
    presente: bool | None


@router.put("/lezioni/{lezione_id}/presenze/{cliente_id}", status_code=204)
def presenza(
    lezione_id: int, cliente_id: int, dati: Presenza,
    _: Utente = Depends(solo_staff), db: Session = Depends(get_db),
) -> None:
    with regole():
        r.segna_presenza(db, lezione_id, cliente_id, dati.presente)


# ------------------------------------------------------------------ clienti
@router.get("/clienti")
def clienti(
    cerca: str = "", _: Utente = Depends(solo_staff), db: Session = Depends(get_db)
) -> list[dict]:
    q = select(Utente).where(Utente.cancellato_il.is_(None), Utente.ruolo == Ruolo.CLIENTE)
    if cerca.strip():
        like = f"%{cerca.strip().lower()}%"
        q = q.where(or_(
            func.lower(Utente.nome + " " + Utente.cognome).like(like),
            func.lower(Utente.email).like(like),
            Utente.telefono.like(like),
        ))
    return [viste.utente(u) for u in db.scalars(q.order_by(Utente.cognome, Utente.nome))]


@router.get("/clienti/{cliente_id}")
def scheda(cliente_id: int, _: Utente = Depends(solo_staff), db: Session = Depends(get_db)) -> dict:
    c = _cliente(db, cliente_id)
    adesso = orario.adesso()
    prenotazioni = db.scalars(
        select(Prenotazione).where(Prenotazione.utente_id == c.id, Prenotazione.stato == StatoPrenotazione.ATTIVA)
        .join(Lezione).order_by(Lezione.inizio.desc()).options(selectinload(Prenotazione.lezione))
    ).all()
    prossime = [p for p in prenotazioni if p.lezione.inizio > adesso][::-1]
    fatte = [p for p in prenotazioni if p.lezione.inizio <= adesso]
    movimenti = db.scalars(
        select(Movimento).where(Movimento.utente_id == c.id)
        .order_by(Movimento.creato_il.desc(), Movimento.id.desc()).limit(40)
    ).all()
    return {
        "cliente": viste.utente(c),
        "prossime": [
            {"lezione_id": p.lezione_id, "inizio": p.lezione.inizio.isoformat(), "titolo": p.lezione.titolo,
             "istruttrice": orario.ISTRUTTRICI[p.lezione.istruttrice]["nome"]}
            for p in prossime
        ],
        "fatte": len(fatte),
        "assenze": sum(1 for p in fatte if p.presente is False),
        "movimenti": [
            {"quando": m.creato_il.isoformat(), "variazione": m.variazione, "saldo": m.saldo,
             "motivo": m.motivo, "autore": m.autore.nome if m.autore else None}
            for m in movimenti
        ],
    }


class Saldo(BaseModel):
    lezioni: int | None = Field(default=None, ge=-50, le=500)
    aggiungi: int | None = Field(default=None, ge=-500, le=500)
    scadenza: date | None = None
    cambia_scadenza: bool = False
    nota: str = Field(default="", max_length=150)


@router.post("/clienti/{cliente_id}/lezioni")
def saldo(
    cliente_id: int, dati: Saldo, autore: Utente = Depends(solo_staff), db: Session = Depends(get_db)
) -> dict:
    c = _cliente(db, cliente_id)
    with regole():
        r.imposta_saldo(
            db, c, autore, lezioni=dati.lezioni, aggiungi=dati.aggiungi,
            scadenza=dati.scadenza, cambia_scadenza=dati.cambia_scadenza, nota=dati.nota,
        )
    return viste.utente(c)


# ------------------------------------------------------------------- avvisi
class NuovoAvviso(BaseModel):
    testo: str = Field(min_length=3, max_length=1000)


@router.get("/avvisi")
def avvisi(_: Utente = Depends(solo_staff), db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": a.id, "testo": a.testo, "quando": a.creato_il.isoformat(), "da": a.autore.nome if a.autore else None}
        for a in db.scalars(select(Avviso).order_by(Avviso.creato_il.desc()).limit(50))
    ]


@router.post("/avvisi", status_code=201)
def pubblica(dati: NuovoAvviso, autore: Utente = Depends(solo_staff), db: Session = Depends(get_db)) -> dict:
    a = Avviso(autore_id=autore.id, testo=dati.testo.strip())
    db.add(a)
    db.commit()
    return {"id": a.id}


@router.delete("/avvisi/{avviso_id}", status_code=204)
def togli_avviso(avviso_id: int, _: Utente = Depends(solo_staff), db: Session = Depends(get_db)) -> None:
    a = db.get(Avviso, avviso_id)
    if a:
        db.delete(a)
        db.commit()


# ------------------------------------------------------------------- numeri
@router.get("/numeri")
def numeri(_: Utente = Depends(solo_staff), db: Session = Depends(get_db)) -> dict:
    """Le ultime quattro settimane: quanto si riempiono le lezioni, quali
    orari tirano di più, quante assenze."""
    da = orario.oggi() - timedelta(days=28)
    lezioni = [l for l in r.lezioni_nel_periodo(db, da, 28) if l.inizio <= orario.adesso() and not l.annullata_il]
    presi = sum(len(l.attive) for l in lezioni)
    posti = sum(l.posti for l in lezioni) or 1
    fasce: dict[str, list[float]] = {}
    for l in lezioni:
        t = orario.locale(l.inizio)
        chiave = f"{'Sab' if t.weekday() == 5 else 'Lun–Ven'} {t:%H:%M}"
        fasce.setdefault(chiave, []).append(len(l.attive) / l.posti)
    clienti_attive = db.scalar(
        select(func.count(Utente.id)).where(Utente.ruolo == Ruolo.CLIENTE, Utente.cancellato_il.is_(None))
    )
    da_saldare = db.scalars(
        select(Utente).where(Utente.lezioni_rimaste < 0, Utente.cancellato_il.is_(None))
        .order_by(Utente.lezioni_rimaste)
    ).all()
    return {
        "lezioni": len(lezioni),
        "riempimento": round(presi / posti * 100),
        "presenze": presi,
        "assenze": sum(1 for l in lezioni for p in l.attive if p.presente is False),
        "fasce": sorted(
            ({"fascia": k, "riempimento": round(sum(v) / len(v) * 100)} for k, v in fasce.items()),
            key=lambda x: -x["riempimento"],
        ),
        "clienti": clienti_attive,
        "da_saldare": [viste.utente(u) for u in da_saldare],
    }
