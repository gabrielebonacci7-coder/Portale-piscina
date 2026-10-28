"""Le regole dello studio, tutte qui.

Prenotare, disdire, la lista d'attesa, il saldo delle lezioni, gli
annullamenti. I router si limitano a chiamare queste funzioni e a tradurre
`ErroreRegola` in una risposta: così le regole si leggono (e si provano) in un
posto solo, senza HTTP di mezzo.

**Un posto, una persona.** Tutte le operazioni che cambiano chi occupa una
lezione passano dal lucchetto `_scrittura`. L'app gira con un solo processo
(vedi Dockerfile), quindi il lucchetto basta a impedire che due clienti
prendano insieme l'ultimo reformer. Il database aggiunge una seconda
garanzia: l'indice unico su (lezione, cliente) per le prenotazioni attive.
"""

import threading
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from reformer.core.config import settings
from reformer.dominio import orario
from reformer.models import (
    Attesa,
    Lezione,
    Movimento,
    Notifica,
    Prenotazione,
    Ruolo,
    StatoPrenotazione,
    TitoloFisso,
    Utente,
)

_scrittura = threading.RLock()


class ErroreRegola(Exception):
    """Una regola dello studio non permette l'operazione.

    `stato` è il codice HTTP che il router restituirà: 404 per ciò che non
    esiste, 409 per un conflitto (lezione piena, troppo tardi per disdire),
    400 per una richiesta sbagliata.
    """

    def __init__(self, messaggio: str, stato: int = 409):
        super().__init__(messaggio)
        self.messaggio = messaggio
        self.stato = stato


# --------------------------------------------------------------- calendario
def assicura_lezioni(db: Session, da: date, giorni: int) -> None:
    """Crea le righe delle lezioni che mancano nel periodo, seguendo l'orario.

    Le lezioni non si creano tutte in anticipo per l'anno: nascono quando
    qualcuno guarda quei giorni. Così se l'orario cambia, i giorni futuri
    seguono il nuovo orario senza dover cancellare niente.
    """
    istanti = [i for g in orario.giorni(da, giorni) for i in orario.orari_del_giorno(g)]
    if not istanti:
        return
    gia = list(db.scalars(select(Lezione).where(Lezione.inizio.in_(istanti))))
    esistenti = {l.inizio for l in gia}
    # Se cambia chi insegna un giorno, le lezioni future già nel calendario si
    # riallineano da sole (quelle passate restano com'erano).
    for l in gia:
        giusta = orario.ISTRUTTRICE_DEL_GIORNO[orario.locale(l.inizio).weekday()]
        if l.istruttrice != giusta and l.inizio > orario.adesso():
            l.istruttrice = giusta
    if db.dirty:
        db.commit()
    titoli = titoli_fissi(db)
    nuove = [
        Lezione(
            inizio=i,
            durata_minuti=orario.DURATA_MINUTI,
            istruttrice=orario.ISTRUTTRICE_DEL_GIORNO[orario.locale(i).weekday()],
            posti=settings.posti_per_lezione,
            titolo=titoli.get(_chiave_settimanale(i), orario.TITOLO_BASE),
        )
        for i in istanti
        if i not in esistenti
    ]
    if nuove:
        db.add_all(nuove)
        db.commit()


# Il calendario si può guardare da un anno indietro a tre mesi avanti. Oltre
# non serve a nessuno, e senza un limite basterebbe chiedere l'anno 3000 per
# far creare al server migliaia di lezioni vuote.
GIORNI_INDIETRO_MAX = 366
GIORNI_AVANTI_MAX = 92


def controlla_periodo(da: date, giorni: int) -> None:
    oggi = orario.oggi()
    if da < oggi - timedelta(days=GIORNI_INDIETRO_MAX) or da + timedelta(days=giorni) > oggi + timedelta(days=GIORNI_AVANTI_MAX):
        raise ErroreRegola("Date fuori dal calendario.", 400)


def _chiave_settimanale(istante: datetime) -> tuple[int, str]:
    t = orario.locale(istante)
    return t.weekday(), f"{t:%H:%M}"


def titoli_fissi(db: Session) -> dict[tuple[int, str], str]:
    """I nomi delle lezioni che si ripetono: quelli di partenza, con sopra
    quelli scelti da Greta ed Elisa."""
    titoli = dict(orario.TITOLI_INIZIALI)
    for t in db.scalars(select(TitoloFisso)):
        titoli[(t.giorno, t.ora)] = t.titolo
    return titoli


def lezioni_nel_periodo(db: Session, da: date, giorni: int) -> list[Lezione]:
    controlla_periodo(da, giorni)
    assicura_lezioni(db, da, giorni)
    inizio = orario.inizio_utc(da, datetime.min.time())
    fine = orario.inizio_utc(da + timedelta(days=giorni), datetime.min.time())
    return list(
        db.scalars(
            select(Lezione)
            .where(Lezione.inizio >= inizio, Lezione.inizio < fine)
            .options(selectinload(Lezione.prenotazioni), selectinload(Lezione.attese))
            .order_by(Lezione.inizio)
        )
    )


def trova_lezione(db: Session, lezione_id: int) -> Lezione:
    lezione = db.get(Lezione, lezione_id)
    if lezione is None:
        raise ErroreRegola("Lezione non trovata", 404)
    return lezione


def fine_lezione(lezione: Lezione) -> datetime:
    return lezione.inizio + timedelta(minutes=lezione.durata_minuti)


def disdicibile(lezione: Lezione) -> bool:
    return lezione.inizio - orario.adesso() >= timedelta(hours=settings.ore_disdetta)


def limite_disdetta(lezione: Lezione) -> datetime:
    return lezione.inizio - timedelta(hours=settings.ore_disdetta)


def prenotazione_attiva(lezione: Lezione, utente_id: int) -> Prenotazione | None:
    return next((p for p in lezione.attive if p.utente_id == utente_id), None)


# ------------------------------------------------------- saldo e notifiche
def notifica(db: Session, utente_id: int, testo: str) -> None:
    db.add(Notifica(utente_id=utente_id, testo=testo))


def notifica_staff(db: Session, testo: str) -> None:
    for sid in db.scalars(select(Utente.id).where(Utente.ruolo == Ruolo.STAFF)):
        notifica(db, sid, testo)


def muovi_saldo(
    db: Session,
    utente: Utente,
    variazione: int,
    motivo: str,
    *,
    autore: Utente | None = None,
    lezione: Lezione | None = None,
) -> None:
    """Cambia le lezioni rimaste e ne lascia traccia."""
    prima = utente.lezioni_rimaste
    utente.lezioni_rimaste = prima + variazione
    db.add(
        Movimento(
            utente_id=utente.id,
            autore_id=autore.id if autore else None,
            variazione=variazione,
            saldo=utente.lezioni_rimaste,
            motivo=motivo,
            lezione_id=lezione.id if lezione else None,
        )
    )
    # Il saldo scende sotto zero: la cliente ha prenotato senza lezioni nel
    # pacchetto. Si può fare, ma Greta ed Elisa devono saperlo per chiederle
    # di saldare in studio.
    if variazione < 0 and utente.lezioni_rimaste < 0 and not utente.e_staff:
        dove = f" ({orario.quando(lezione.inizio)})" if lezione else ""
        notifica_staff(
            db,
            f"{utente.nome_completo} ha prenotato senza lezioni nel pacchetto{dove}: "
            f"saldo {utente.lezioni_rimaste}. Da saldare in studio.",
        )


# --------------------------------------------------------------- prenotare
def _iscrivi(
    db: Session,
    lezione: Lezione,
    utente: Utente,
    *,
    dalla_lista: bool = False,
    da_staff: Utente | None = None,
) -> Prenotazione:
    p = Prenotazione(
        lezione_id=lezione.id,
        utente_id=utente.id,
        dalla_lista=dalla_lista,
        aggiunta_da_staff=da_staff is not None,
    )
    db.add(p)
    lezione.prenotazioni.append(p)
    # Chi entra non è più in attesa per la stessa lezione.
    for a in list(lezione.attese):
        if a.utente_id == utente.id:
            lezione.attese.remove(a)
            db.delete(a)
    motivo = "Prenotazione" if da_staff is None else f"Aggiunta da {da_staff.nome}"
    if dalla_lista:
        motivo = "Entrata dalla lista d'attesa"
    muovi_saldo(db, utente, -1, motivo, autore=da_staff, lezione=lezione)
    return p


def controlla_pacchetto(utente: Utente) -> None:
    """A pacchetto finito non si prenota (e non si entra in lista d'attesa)."""
    if utente.lezioni_rimaste - 1 < -settings.max_lezioni_da_saldare:
        raise ErroreRegola(
            "Hai finito le lezioni del pacchetto: rinnovalo in studio con Greta o Elisa "
            "e poi potrai prenotare di nuovo."
        )


def prenota(db: Session, lezione_id: int, utente: Utente) -> Prenotazione:
    with _scrittura:
        lezione = trova_lezione(db, lezione_id)
        db.refresh(lezione)
        if lezione.annullata_il:
            raise ErroreRegola("Questa lezione è stata annullata.")
        if lezione.inizio <= orario.adesso():
            raise ErroreRegola("La lezione è già iniziata.")
        if orario.locale(lezione.inizio).date() > orario.ultimo_giorno_prenotabile():
            raise ErroreRegola(f"Si può prenotare al massimo {settings.giorni_prenotabili} giorni prima.")
        if prenotazione_attiva(lezione, utente.id):
            raise ErroreRegola("Sei già iscritta a questa lezione.")
        if lezione.liberi <= 0:
            raise ErroreRegola("La lezione è piena: puoi metterti in lista d'attesa.")
        controlla_pacchetto(utente)
        p = _iscrivi(db, lezione, utente)
        db.commit()
        return p


def disdici(db: Session, lezione_id: int, utente: Utente) -> Utente | None:
    """La cliente toglie la sua prenotazione. Ritorna chi entra dalla lista."""
    with _scrittura:
        lezione = trova_lezione(db, lezione_id)
        db.refresh(lezione)
        p = prenotazione_attiva(lezione, utente.id)
        if p is None:
            raise ErroreRegola("Non risulti iscritta a questa lezione.", 404)
        if not disdicibile(lezione):
            raise ErroreRegola(
                f"Mancano meno di {settings.ore_disdetta} ore: la lezione non si può più disdire. "
                f"Per un'emergenza avvisa {orario.ISTRUTTRICI[lezione.istruttrice]['nome']}."
            )
        entrata = _libera_posto(db, lezione, p, StatoPrenotazione.DISDETTA, "Disdetta")
        db.commit()
        return entrata


def _libera_posto(
    db: Session,
    lezione: Lezione,
    p: Prenotazione,
    stato: StatoPrenotazione,
    motivo: str,
    autore: Utente | None = None,
) -> Utente | None:
    """Chiude una prenotazione, restituisce la lezione e fa entrare la prima
    della lista d'attesa (se la lezione non è già cominciata)."""
    p.stato = stato
    p.chiusa_il = orario.adesso()
    muovi_saldo(db, p.utente, +1, motivo, autore=autore, lezione=lezione)
    if lezione.annullata_il or lezione.inizio <= orario.adesso() or not lezione.attese:
        return None
    # Entra la prima della lista che può ancora prenotare: chi ha già il
    # massimo di lezioni da saldare resta in lista e passa la successiva.
    prima = next(
        (a for a in lezione.attese if a.utente.lezioni_rimaste - 1 >= -settings.max_lezioni_da_saldare),
        None,
    )
    if prima is None:
        return None
    entrata = prima.utente
    _iscrivi(db, lezione, entrata, dalla_lista=True)
    notifica(
        db,
        entrata.id,
        f"Si è liberato un posto: sei dentro alla lezione di {orario.quando(lezione.inizio)}! "
        + (
            f"Se non puoi venire, disdici entro {orario.quando(limite_disdetta(lezione))}."
            if disdicibile(lezione)
            else f"Mancano meno di {settings.ore_disdetta} ore: se non puoi venire scrivi allo studio."
        ),
    )
    return entrata


# ---------------------------------------------------------- lista d'attesa
def entra_in_attesa(db: Session, lezione_id: int, utente: Utente) -> int:
    """Ritorna la posizione in lista (1 = la prima)."""
    with _scrittura:
        lezione = trova_lezione(db, lezione_id)
        db.refresh(lezione)
        if lezione.annullata_il or lezione.inizio <= orario.adesso():
            raise ErroreRegola("Per questa lezione non c'è più la lista d'attesa.")
        if prenotazione_attiva(lezione, utente.id):
            raise ErroreRegola("Sei già iscritta a questa lezione.")
        if lezione.liberi > 0:
            raise ErroreRegola("C'è ancora posto: puoi prenotare direttamente.")
        controlla_pacchetto(utente)
        ids = [a.utente_id for a in lezione.attese]
        if utente.id in ids:
            return ids.index(utente.id) + 1
        db.add(Attesa(lezione_id=lezione.id, utente_id=utente.id))
        db.commit()
        db.refresh(lezione)
        return [a.utente_id for a in lezione.attese].index(utente.id) + 1


def esci_dall_attesa(db: Session, lezione_id: int, utente: Utente) -> None:
    with _scrittura:
        lezione = trova_lezione(db, lezione_id)
        for a in list(lezione.attese):
            if a.utente_id == utente.id:
                db.delete(a)
        db.commit()


# ----------------------------------------------------------------- lo staff
def staff_aggiungi(db: Session, lezione_id: int, cliente: Utente, autore: Utente) -> Prenotazione:
    """Greta o Elisa iscrivono una cliente (per esempio chi ha chiamato).

    Valgono le stesse regole sui posti, ma non il limite del mese: lo studio
    può segnare anche una lezione lontana.
    """
    with _scrittura:
        lezione = trova_lezione(db, lezione_id)
        db.refresh(lezione)
        if lezione.annullata_il:
            raise ErroreRegola("La lezione è annullata: rimettila in calendario prima.")
        if prenotazione_attiva(lezione, cliente.id):
            raise ErroreRegola(f"{cliente.nome_completo} è già iscritta.")
        if lezione.liberi <= 0:
            raise ErroreRegola("La lezione è piena.")
        p = _iscrivi(db, lezione, cliente, da_staff=autore)
        notifica(
            db, cliente.id,
            f"{autore.nome} ti ha iscritta alla lezione di {orario.quando(lezione.inizio)}.",
        )
        db.commit()
        return p


def staff_togli(db: Session, lezione_id: int, cliente_id: int, autore: Utente) -> Utente | None:
    """Lo studio toglie una cliente: senza limite di 12 ore, e la lezione le
    torna nel pacchetto. Ritorna chi entra dalla lista d'attesa."""
    with _scrittura:
        lezione = trova_lezione(db, lezione_id)
        db.refresh(lezione)
        p = prenotazione_attiva(lezione, cliente_id)
        if p is None:
            raise ErroreRegola("Questa cliente non è iscritta.", 404)
        entrata = _libera_posto(
            db, lezione, p, StatoPrenotazione.TOLTA, f"Tolta da {autore.nome}", autore=autore
        )
        notifica(
            db, cliente_id,
            f"{autore.nome} ti ha tolta dalla lezione di {orario.quando(lezione.inizio)}: "
            "la lezione è tornata nel tuo pacchetto.",
        )
        db.commit()
        return entrata


def annulla_lezione(db: Session, lezione_id: int, motivo: str, autore: Utente) -> int:
    """Annulla la lezione: chi era iscritta riavrà la lezione ed è avvisata,
    e anche chi era in attesa lo viene a sapere. Ritorna quante erano iscritte."""
    with _scrittura:
        lezione = trova_lezione(db, lezione_id)
        db.refresh(lezione)
        if lezione.annullata_il:
            return 0
        lezione.annullata_il = orario.adesso()
        lezione.motivo_annullamento = motivo or None
        perche = f": {motivo}" if motivo else ""
        iscritte = list(lezione.attive)
        for p in iscritte:
            p.stato = StatoPrenotazione.ANNULLATA
            p.chiusa_il = orario.adesso()
            muovi_saldo(db, p.utente, +1, "Lezione annullata dallo studio", autore=autore, lezione=lezione)
            notifica(
                db, p.utente_id,
                f"La lezione di {orario.quando(lezione.inizio)} è annullata{perche}. "
                "La lezione è tornata nel tuo pacchetto.",
            )
        for a in list(lezione.attese):
            notifica(db, a.utente_id, f"La lezione di {orario.quando(lezione.inizio)} è annullata{perche}.")
            db.delete(a)
        db.commit()
        return len(iscritte)


def aggiungi_lezione(db: Session, giorno: date, ora: str, titolo: str = "") -> Lezione:
    """Greta o Elisa aprono una lezione fuori dall'orario fisso (per esempio
    alle 18:30). Resta in calendario come le altre: si prenota, si annulla,
    ha la sua lista d'attesa."""
    with _scrittura:
        try:
            hh, mm = (int(x) for x in ora.split(":"))
            inizio = orario.inizio_utc(giorno, datetime.min.time().replace(hour=hh, minute=mm))
        except (ValueError, TypeError):
            raise ErroreRegola("Ora non valida: scrivila come 18:30.", 400) from None
        if giorno.weekday() == 6:
            raise ErroreRegola("La domenica lo studio è chiuso.", 400)
        if inizio <= orario.adesso():
            raise ErroreRegola("Quest'ora è già passata.", 400)
        controlla_periodo(giorno, 1)
        if db.scalar(select(Lezione.id).where(Lezione.inizio == inizio)):
            raise ErroreRegola("A quest'ora c'è già una lezione.")
        lezione = Lezione(
            inizio=inizio,
            durata_minuti=orario.DURATA_MINUTI,
            istruttrice=orario.ISTRUTTRICE_DEL_GIORNO[giorno.weekday()],
            posti=settings.posti_per_lezione,
            titolo=(titolo or "").strip()[:60] or titoli_fissi(db).get((giorno.weekday(), ora), orario.TITOLO_BASE),
        )
        db.add(lezione)
        db.commit()
        return lezione


def ripristina_lezione(db: Session, lezione_id: int) -> None:
    """Rimette in calendario una lezione annullata. Chi era iscritta non
    rientra da sola: ha già riavuto la lezione e potrebbe aver preso altro."""
    with _scrittura:
        lezione = trova_lezione(db, lezione_id)
        lezione.annullata_il = None
        lezione.motivo_annullamento = None
        db.commit()


def cambia_titolo(db: Session, lezione_id: int, titolo: str, ogni_settimana: bool = False) -> Lezione:
    """Cambia il nome di una lezione, o di quella lezione tutte le settimane.

    Con `ogni_settimana` il nome vale per quel giorno e quell'ora d'ora in
    poi: le lezioni future già nel calendario si aggiornano, e quelle che
    nasceranno lo prendono da sole. Le lezioni passate restano com'erano.
    """
    lezione = trova_lezione(db, lezione_id)
    titolo = (titolo or "").strip()[:60] or orario.TITOLO_BASE
    lezione.titolo = titolo
    if ogni_settimana:
        giorno, ora = _chiave_settimanale(lezione.inizio)
        fisso = db.scalar(select(TitoloFisso).where(TitoloFisso.giorno == giorno, TitoloFisso.ora == ora))
        if fisso is None:
            db.add(TitoloFisso(giorno=giorno, ora=ora, titolo=titolo))
        else:
            fisso.titolo = titolo
        for altra in db.scalars(select(Lezione).where(Lezione.inizio > orario.adesso())):
            if _chiave_settimanale(altra.inizio) == (giorno, ora):
                altra.titolo = titolo
    db.commit()
    return lezione


def segna_presenza(db: Session, lezione_id: int, cliente_id: int, presente: bool | None) -> None:
    lezione = trova_lezione(db, lezione_id)
    p = prenotazione_attiva(lezione, cliente_id)
    if p is None:
        raise ErroreRegola("Questa cliente non è iscritta.", 404)
    p.presente = presente
    db.commit()


def imposta_saldo(
    db: Session,
    cliente: Utente,
    autore: Utente,
    *,
    lezioni: int | None = None,
    aggiungi: int | None = None,
    scadenza: date | None = None,
    cambia_scadenza: bool = False,
    nota: str = "",
) -> Utente:
    """Greta o Elisa scrivono quante lezioni restano a una cliente.

    Si può dare il numero esatto (`lezioni`) oppure quante aggiungerne o
    toglierne (`aggiungi`, anche negativo). La differenza finisce nei
    movimenti con il nome di chi l'ha fatta.
    """
    with _scrittura:
        if lezioni is not None and aggiungi is not None:
            raise ErroreRegola("Indica il numero di lezioni oppure quante aggiungerne, non tutti e due.", 400)
        variazione = 0
        if lezioni is not None:
            variazione = lezioni - cliente.lezioni_rimaste
        elif aggiungi is not None:
            variazione = aggiungi
        if variazione:
            motivo = nota.strip()[:150] or (
                f"{'Caricate' if variazione > 0 else 'Tolte'} da {autore.nome}"
            )
            muovi_saldo(db, cliente, variazione, motivo, autore=autore)
            if variazione > 0:
                notifica(
                    db, cliente.id,
                    f"{autore.nome} ha aggiornato il tuo pacchetto: ora hai "
                    f"{max(cliente.lezioni_rimaste, 0)} lezioni disponibili.",
                )
        if cambia_scadenza:
            cliente.scadenza = scadenza
        db.commit()
        return cliente
