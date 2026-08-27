"""Le regole delle prenotazioni: disponibilità, conto, creazione, annullamento.

Qui non si sa niente di HTTP. I router traducono in codici di stato le due
eccezioni che escono da questo modulo, e i test le provano senza passare per
la rete.
"""

import secrets
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from piscina.core.config import settings
from piscina.dominio import listino
from piscina.dominio.disponibilita import (
    FASCE,
    GIORNATA,
    MATTINA,
    POMERIGGIO,
    fascia_conclusa,
)
from piscina.dominio.orologio import adesso, oggi
from piscina.models import (
    ANNULLATA,
    IN_ATTESA,
    MEZZE,
    Occupazione,
    Postazione,
    Prenotazione,
    RigaPrenotazione,
)

# Alfabeto senza le lettere che si confondono al telefono: niente O contro 0,
# niente I contro 1. Il codice si detta in cassa, deve arrivare intero.
ALFABETO = "ACDEFGHJKLMNPQRTUVWXY34679"
LUNGHEZZA_CODICE = 5


class RichiestaNonValida(ValueError):
    """La richiesta è sbagliata: data fuori stagione, troppi lettini, ecc."""


class PostoOccupato(RuntimeError):
    """Qualcuno l'ha presa prima. Si torna alla mappa e si sceglie un'altra."""

    def __init__(self, codici: list[str]):
        self.codici = codici
        elenco = ", ".join(codici)
        if len(codici) == 1:
            messaggio = f"La postazione {elenco} nel frattempo è stata presa da qualcun altro"
        else:
            messaggio = f"Le postazioni {elenco} nel frattempo sono state prese da qualcun altro"
        super().__init__(messaggio)


@dataclass
class Scelta:
    """Una postazione scelta sulla mappa, con quanti lettini ci vanno sotto."""

    codice: str
    lettini: int = 0


# --- Fasce e mezze giornate ------------------------------------------------
def mezze_di(fascia: str) -> tuple[str, ...]:
    """Le metà di giornata che una fascia occupa."""
    if fascia == GIORNATA:
        return MEZZE
    return (fascia,)


# --- Disponibilità ---------------------------------------------------------
def occupazione_del_giorno(db: Session, giorno: date) -> dict[int, set[str]]:
    """Per ogni postazione, quali metà di giornata sono già prese."""
    presi: dict[int, set[str]] = {}
    righe = db.execute(
        select(Occupazione.postazione_id, Occupazione.mezza).where(
            Occupazione.giorno == giorno
        )
    )
    for postazione_id, mezza in righe:
        presi.setdefault(postazione_id, set()).add(mezza)
    return presi


def mappa_del_giorno(db: Session, giorno: date) -> list[dict]:
    """Lo stato di ogni postazione in un giorno: è quello che colora la mappa.

    Si restituiscono le due metà separate invece di un colore già deciso:
    così l'app può dire "libera solo la mattina" invece di un generico
    "occupata", e chi cerca mezza giornata vede subito dove può stare.
    """
    presi = occupazione_del_giorno(db, giorno)
    postazioni = db.scalars(select(Postazione).order_by(Postazione.codice)).all()

    mappa = []
    for p in postazioni:
        occupate = presi.get(p.id, set())
        libera_mattina = p.attiva and MATTINA not in occupate
        libera_pomeriggio = p.attiva and POMERIGGIO not in occupate
        mappa.append(
            {
                "codice": p.codice,
                "tipo": p.tipo,
                "fila": p.fila,
                "x": p.x,
                "y": p.y,
                "max_lettini": p.max_lettini,
                "attiva": p.attiva,
                "nota": p.nota,
                "libera_mattina": libera_mattina,
                "libera_pomeriggio": libera_pomeriggio,
            }
        )
    return mappa


# --- Prezzi ----------------------------------------------------------------
def prezzo_riga_cent(tipo: str, lettini: int, fascia: str) -> int:
    """Quanto costa una postazione per una fascia.

    Il listino ha una tariffa sola, "al giorno": finché non ne esiste una per
    la mezza giornata, mattina e pomeriggio costano come la giornata intera.
    Il giorno che si decide di scontarle, si imposta PISCINA_SCONTO_MEZZA_
    GIORNATA e non si tocca nient'altro.
    """
    base = listino.prezzo_cent(tipo, lettini)
    if fascia == GIORNATA or not settings.sconto_mezza_giornata:
        return base
    return round(base * (1 - settings.sconto_mezza_giornata))


# --- Creazione -------------------------------------------------------------
def _codice_nuovo(db: Session) -> str:
    for _ in range(20):
        codice = "PC-" + "".join(secrets.choice(ALFABETO) for _ in range(LUNGHEZZA_CODICE))
        if not db.scalar(select(Prenotazione.id).where(Prenotazione.codice == codice)):
            return codice
    raise RuntimeError("non riesco a generare un codice prenotazione libero")


def _controlla_giorno(giorno: date, fascia: str) -> None:
    if fascia not in FASCE:
        raise RichiestaNonValida(f"fascia sconosciuta: {fascia}")

    if giorno < oggi():
        raise RichiestaNonValida("Non si può prenotare un giorno passato")

    if fascia_conclusa(giorno, fascia, adesso()):
        raise RichiestaNonValida("Questa fascia oraria è già finita per oggi")

    limite = settings.giorni_prenotabili
    if (giorno - oggi()).days > limite:
        raise RichiestaNonValida(f"Si prenota al massimo {limite} giorni in anticipo")

    inizio, fine = settings.stagione_inizio, settings.stagione_fine
    if (inizio and giorno < inizio) or (fine and giorno > fine):
        raise RichiestaNonValida("La piscina è chiusa in questa data")


def _controlla_scelte(db: Session, scelte: list[Scelta]) -> list[tuple[Postazione, int]]:
    if not scelte:
        raise RichiestaNonValida("Scegli almeno una postazione sulla mappa")

    massimo = settings.max_postazioni_per_prenotazione
    if len(scelte) > massimo:
        raise RichiestaNonValida(
            f"Al massimo {massimo} postazioni per prenotazione. "
            "Per un gruppo più grande, chiamaci."
        )

    codici = [s.codice.strip().upper() for s in scelte]
    if len(set(codici)) != len(codici):
        raise RichiestaNonValida("Hai scelto due volte la stessa postazione")

    trovate = {
        p.codice: p
        for p in db.scalars(select(Postazione).where(Postazione.codice.in_(codici)))
    }

    risultato = []
    for scelta, codice in zip(scelte, codici, strict=True):
        postazione = trovate.get(codice)
        if postazione is None:
            raise RichiestaNonValida(f"La postazione {codice} non esiste")
        if not postazione.attiva:
            raise RichiestaNonValida(f"La postazione {codice} non è disponibile")

        lettini = int(scelta.lettini or 0)
        if postazione.tipo == "lettino":
            # Il lettino del solarium è già un lettino: non ne porta altri.
            lettini = 0
        elif not 0 <= lettini <= postazione.max_lettini:
            raise RichiestaNonValida(
                f"Sotto un ombrellone stanno al massimo {postazione.max_lettini} lettini"
            )
        risultato.append((postazione, lettini))
    return risultato


def crea(
    db: Session,
    *,
    giorno: date,
    fascia: str,
    scelte: list[Scelta],
    nome: str,
    telefono: str,
    email: str,
    persone: int = 1,
    note: str = "",
) -> Prenotazione:
    """Registra una prenotazione, o dice perché non si può."""
    _controlla_giorno(giorno, fascia)
    postazioni = _controlla_scelte(db, scelte)

    prenotazione = Prenotazione(
        codice=_codice_nuovo(db),
        giorno=giorno,
        fascia=fascia,
        nome=nome.strip(),
        telefono=telefono.strip(),
        email=email.strip().lower(),
        persone=persone,
        note=note.strip(),
        stato=IN_ATTESA,
        totale_cent=0,
    )

    totale = 0
    for postazione, lettini in postazioni:
        prezzo = prezzo_riga_cent(postazione.tipo, lettini, fascia)
        totale += prezzo
        riga = RigaPrenotazione(
            postazione_id=postazione.id, lettini=lettini, prezzo_cent=prezzo
        )
        riga.occupazioni = [
            Occupazione(postazione_id=postazione.id, giorno=giorno, mezza=mezza)
            for mezza in mezze_di(fascia)
        ]
        prenotazione.righe.append(riga)
    prenotazione.totale_cent = totale

    db.add(prenotazione)
    try:
        db.commit()
    except IntegrityError:
        # Ci è arrivato prima qualcun altro: il vincolo su (postazione, giorno,
        # mezza) ha respinto la scrittura. Si rilegge chi è rimasto libero e si
        # dice all'utente quali postazioni deve cambiare.
        db.rollback()
        raise PostoOccupato(_gia_prese(db, giorno, fascia, [p for p, _ in postazioni])) from None

    db.refresh(prenotazione)
    return prenotazione


def _gia_prese(
    db: Session, giorno: date, fascia: str, postazioni: list[Postazione]
) -> list[str]:
    presi = occupazione_del_giorno(db, giorno)
    volute = set(mezze_di(fascia))
    return sorted(p.codice for p in postazioni if presi.get(p.id, set()) & volute)


# --- Lettura e annullamento ------------------------------------------------
def per_codice(db: Session, codice: str) -> Prenotazione | None:
    return db.scalar(
        select(Prenotazione).where(Prenotazione.codice == codice.strip().upper())
    )


def _solo_cifre(telefono: str) -> str:
    return "".join(c for c in telefono if c.isdigit())


def per_codice_e_telefono(db: Session, codice: str, telefono: str) -> Prenotazione | None:
    """Il cliente ritrova la sua prenotazione con il codice e il suo numero.

    Il numero fa da password: senza, chi indovina un codice leggerebbe nome ed
    email di uno sconosciuto. Si confrontano le sole cifre, perché lo stesso
    numero si scrive in cinque modi diversi (+39, spazi, trattini).
    """
    prenotazione = per_codice(db, codice)
    if prenotazione is None:
        return None
    atteso = _solo_cifre(prenotazione.telefono)
    dato = _solo_cifre(telefono)
    # Confronto sulle ultime nove cifre: è il numero italiano senza prefisso.
    if not dato or atteso[-9:] != dato[-9:]:
        return None
    return prenotazione


def del_giorno(db: Session, giorno: date) -> list[Prenotazione]:
    return list(
        db.scalars(
            select(Prenotazione)
            .where(Prenotazione.giorno == giorno)
            .order_by(Prenotazione.creato_il)
        )
    )


def annulla(db: Session, prenotazione: Prenotazione) -> Prenotazione:
    """Annulla e libera subito i posti."""
    if prenotazione.stato == ANNULLATA:
        return prenotazione
    prenotazione.stato = ANNULLATA
    for riga in prenotazione.righe:
        riga.occupazioni.clear()
    db.commit()
    db.refresh(prenotazione)
    return prenotazione


def cambia_stato(db: Session, prenotazione: Prenotazione, stato: str) -> Prenotazione:
    if stato == ANNULLATA:
        return annulla(db, prenotazione)
    prenotazione.stato = stato
    db.commit()
    db.refresh(prenotazione)
    return prenotazione
