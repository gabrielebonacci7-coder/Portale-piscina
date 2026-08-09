"""Query e regole del pannello di gestione.

Tutto quello che lo staff può fare passa da qui, e ogni modifica lascia una
riga nel registro: le azioni sugli account altrui non devono essere silenziose.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Annuncio,
    AzioneStaff,
    Brevetto,
    ProfiloBagnino,
    ProfiloPiscina,
    Ruolo,
    StatoAnnuncio,
    TipoAzioneStaff,
    TipoUtente,
    Utente,
)


def riepilogo(db: Session) -> dict:
    """I conteggi della schermata iniziale."""

    def conta(query) -> int:
        return db.scalar(query) or 0

    return {
        "utenti": conta(select(func.count(Utente.id))),
        "bagnini": conta(
            select(func.count(Utente.id)).where(Utente.tipo == TipoUtente.BAGNINO)
        ),
        "piscine": conta(
            select(func.count(Utente.id)).where(Utente.tipo == TipoUtente.PISCINA)
        ),
        "sospesi": conta(select(func.count(Utente.id)).where(Utente.attivo.is_(False))),
        "brevetti_da_verificare": conta(
            select(func.count(Brevetto.id)).where(Brevetto.verificato.is_(False))
        ),
        "utenti_da_verificare": conta(
            select(func.count(Utente.id)).where(
                Utente.verificato.is_(False), Utente.attivo.is_(True)
            )
        ),
        "annunci_aperti": conta(
            select(func.count(Annuncio.id)).where(Annuncio.stato == StatoAnnuncio.APERTO)
        ),
    }


def cerca_utenti(
    db: Session,
    *,
    q: str | None = None,
    tipo: TipoUtente | None = None,
    solo_sospesi: bool = False,
    solo_da_verificare: bool = False,
    skip: int = 0,
    limit: int = 30,
) -> tuple[int, list[Utente]]:
    """Elenco account filtrabile. `q` cerca in email, telefono e nome del profilo."""
    condizioni = []
    if tipo is not None:
        condizioni.append(Utente.tipo == tipo)
    if solo_sospesi:
        condizioni.append(Utente.attivo.is_(False))
    if solo_da_verificare:
        condizioni.append(Utente.verificato.is_(False))

    if q:
        testo = f"%{q.strip().lower()}%"
        # I nomi stanno nei profili, che sono due tabelle diverse: si passa da
        # due sottoquery invece che da una join, che con l'outer join doppio
        # duplicherebbe le righe.
        bagnini = select(ProfiloBagnino.utente_id).where(
            func.lower(ProfiloBagnino.nome + " " + ProfiloBagnino.cognome).like(testo)
        )
        piscine = select(ProfiloPiscina.utente_id).where(
            func.lower(ProfiloPiscina.nome_struttura).like(testo)
        )
        condizioni.append(
            or_(
                func.lower(Utente.email).like(testo),
                Utente.telefono.like(testo),
                Utente.id.in_(bagnini),
                Utente.id.in_(piscine),
            )
        )

    base = select(Utente).where(*condizioni)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    elementi = list(
        db.scalars(
            base.options(
                selectinload(Utente.profilo_bagnino).selectinload(ProfiloBagnino.brevetti),
                selectinload(Utente.profilo_piscina),
            )
            .order_by(Utente.creato_il.desc(), Utente.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )
    return totale, elementi


def brevetti(
    db: Session,
    *,
    solo_da_verificare: bool = True,
    skip: int = 0,
    limit: int = 30,
) -> tuple[int, list[Brevetto]]:
    """Coda dei brevetti da controllare, i più vecchi per primi.

    L'ordine è voluto: chi ha caricato il documento tre settimane fa aspetta
    da più tempo di chi lo ha caricato stamattina.
    """
    condizioni = []
    if solo_da_verificare:
        condizioni.append(Brevetto.verificato.is_(False))

    base = select(Brevetto).where(*condizioni)
    totale = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    elementi = list(
        db.scalars(
            base.options(selectinload(Brevetto.bagnino).selectinload(ProfiloBagnino.utente))
            .order_by(Brevetto.creato_il.asc(), Brevetto.id.asc())
            .offset(skip)
            .limit(limit)
        )
    )
    return totale, elementi


def registra(
    db: Session,
    staff: Utente,
    azione: TipoAzioneStaff,
    *,
    oggetto_tipo: str,
    oggetto_id: int,
    oggetto_etichetta: str | None = None,
    motivo: str | None = None,
) -> AzioneStaff:
    """Aggiunge una riga al registro. Non fa commit: lo fa chi chiama."""
    riga = AzioneStaff(
        staff_id=staff.id,
        staff_email=staff.email,
        azione=azione,
        oggetto_tipo=oggetto_tipo,
        oggetto_id=oggetto_id,
        oggetto_etichetta=oggetto_etichetta,
        motivo=motivo,
    )
    db.add(riga)
    return riga


def verifica_brevetto(
    db: Session, staff: Utente, brevetto: Brevetto, valore: bool, motivo: str | None = None
) -> Brevetto:
    brevetto.verificato = valore
    registra(
        db,
        staff,
        TipoAzioneStaff.BREVETTO_VERIFICATO if valore else TipoAzioneStaff.BREVETTO_NON_VERIFICATO,
        oggetto_tipo="brevetto",
        oggetto_id=brevetto.id,
        oggetto_etichetta=f"{brevetto.tipo.value} di {brevetto.bagnino.nome_completo}",
        motivo=motivo,
    )
    db.commit()
    db.refresh(brevetto)
    return brevetto


def verifica_utente(
    db: Session, staff: Utente, utente: Utente, valore: bool, motivo: str | None = None
) -> Utente:
    utente.verificato = valore
    registra(
        db,
        staff,
        TipoAzioneStaff.UTENTE_VERIFICATO if valore else TipoAzioneStaff.UTENTE_NON_VERIFICATO,
        oggetto_tipo="utente",
        oggetto_id=utente.id,
        oggetto_etichetta=utente.nome_visualizzato,
        motivo=motivo,
    )
    db.commit()
    db.refresh(utente)
    return utente


def imposta_stato(
    db: Session, staff: Utente, utente: Utente, attivo: bool, motivo: str | None = None
) -> Utente:
    """Sospende o riattiva un account.

    Sospendere non cancella niente: annunci, messaggi e recensioni restano, ma
    il token smette di funzionare (`get_current_user` blocca gli inattivi).
    Una sospensione sbagliata si annulla rimettendo `attivo` a True.
    """
    utente.attivo = attivo
    registra(
        db,
        staff,
        TipoAzioneStaff.UTENTE_RIATTIVATO if attivo else TipoAzioneStaff.UTENTE_SOSPESO,
        oggetto_tipo="utente",
        oggetto_id=utente.id,
        oggetto_etichetta=utente.nome_visualizzato,
        motivo=motivo,
    )
    db.commit()
    db.refresh(utente)
    return utente


def registro(
    db: Session, *, skip: int = 0, limit: int = 30
) -> tuple[int, list[AzioneStaff]]:
    """Storico delle azioni, dalla più recente."""
    totale = db.scalar(select(func.count(AzioneStaff.id))) or 0
    elementi = list(
        db.scalars(
            select(AzioneStaff)
            .order_by(AzioneStaff.creato_il.desc(), AzioneStaff.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )
    return totale, elementi


def conta_staff(db: Session) -> int:
    return db.scalar(select(func.count(Utente.id)).where(Utente.ruolo == Ruolo.STAFF)) or 0
