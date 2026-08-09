"""Due diritti che la legge riconosce a chi si iscrive: riavere i propri dati
e farli sparire.

**Perché la cancellazione non è un `DELETE`.** Cancellare la riga porterebbe
via, a cascata, anche cose che non appartengono solo a chi se ne va:

- le **recensioni che ha scritto** sono la reputazione di chi le ha ricevute —
  un bagnino che se ne va non deve poter azzerare i giudizi che ha dato a dieci
  piscine, e nemmeno regalarglieli;
- i **messaggi** sono metà di una conversazione: sparirebbe il filo del
  discorso anche all'altra persona, che non ha chiesto niente;
- i **turni già svolti** sono la storia lavorativa della struttura.

Quindi si cancellano i **dati personali**, non le tracce delle interazioni: il
nome sparisce, resta "Utente cancellato". È l'anonimizzazione, ed è il modo
normale di conciliare il diritto alla cancellazione con i diritti degli altri.
Quello che se ne va è tutto ciò che permette di risalire alla persona.
"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.immagini import elimina_immagine
from app.core.privacy import DOMINIO_ANONIMO
from app.db.base_class import utcnow
from app.models import FotoPiscina, Messaggio, StatoAnnuncio, Utente


# --- Diritto di accesso e portabilità --------------------------------------
def _leggibile(valore):
    """Rende serializzabile quello che finisce nell'esportazione."""
    if isinstance(valore, (datetime, date, time)):
        return valore.isoformat()
    if isinstance(valore, Enum):
        return valore.value
    if isinstance(valore, Decimal):
        # I compensi sono Numeric: float qui va bene, è un documento da leggere.
        return float(valore)
    return valore


def _righe(oggetto, campi: list[str]) -> dict:
    return {c: _leggibile(getattr(oggetto, c)) for c in campi}


def esporta(db: Session, utente: Utente) -> dict:
    """Tutto quello che la piattaforma sa di questa persona, in un solo file.

    Deve essere **leggibile da un essere umano**, non solo da un programma: chi
    scarica i propri dati vuole capirci qualcosa, non ricevere un dump.
    Gli id interni restano perché senza non si capirebbe cosa si riferisce a
    cosa.
    """
    dati: dict = {
        "esportato_il": utcnow().isoformat(),
        "account": _righe(
            utente,
            [
                "id", "email", "telefono", "tipo", "ruolo", "attivo",
                "email_verificata", "verificato", "telefono_pubblico",
                "privacy_accettata_il", "privacy_versione", "creato_il",
            ],
        ),
    }

    if utente.profilo_bagnino:
        b = utente.profilo_bagnino
        dati["profilo"] = _righe(
            b,
            ["id", "nome", "cognome", "data_nascita", "citta", "note_spostamenti",
             "anni_esperienza", "bio", "disponibile_chiamata_singola", "cerca_lavoro",
             "creato_il"],
        )
        dati["profilo"]["foto"] = b.foto_url
        dati["profilo"]["zone"] = [z.nome for z in b.zone]
        dati["brevetti"] = [
            _righe(x, ["id", "tipo", "ente", "numero", "data_rilascio",
                       "data_scadenza", "verificato"])
            for x in b.brevetti
        ]
        dati["esperienze"] = [
            _righe(x, ["id", "struttura", "zona", "mansione", "data_inizio",
                       "data_fine", "stagioni", "descrizione"])
            for x in b.esperienze
        ]
        dati["disponibilita"] = [
            _righe(x, ["id", "giorno_settimana", "ora_inizio", "ora_fine", "note"])
            for x in b.disponibilita
        ]

    if utente.profilo_piscina:
        p = utente.profilo_piscina
        dati["profilo"] = _righe(
            p,
            ["id", "nome_struttura", "tipo_struttura", "citta", "indirizzo",
             "partita_iva", "numero_vasche", "descrizione", "referente_nome",
             "referente_ruolo", "referente_telefono", "referente_email",
             "attiva", "creato_il"],
        )
        dati["profilo"]["zona"] = p.zona.nome if p.zona else None
        dati["foto"] = [
            {"id": f.id, "tipo": f.tipo.value, "didascalia": f.didascalia, "url": f.url}
            for f in p.foto
        ]

    dati["annunci_pubblicati"] = [
        _righe(a, ["id", "titolo", "note", "data_inizio", "data_fine", "citta",
                   "indirizzo", "compenso", "compenso_tipo", "tipo_turno",
                   "stato", "creato_il"])
        for a in utente.annunci
    ]
    dati["candidature_inviate"] = [
        {**_righe(c, ["id", "stato", "messaggio", "creato_il"]),
         "annuncio": c.annuncio.titolo if c.annuncio else None}
        for c in utente.candidature
    ]
    dati["recensioni_scritte"] = [
        {**_righe(r, ["id", "stelle", "commento", "voto_puntualita",
                      "voto_professionalita", "voto_ambiente", "voto_pagamento",
                      "creato_il"]),
         "a": r.destinatario.nome_visualizzato}
        for r in utente.recensioni_scritte
    ]
    dati["recensioni_ricevute"] = [
        {**_righe(r, ["id", "stelle", "commento", "creato_il"]),
         "da": r.autore.nome_visualizzato}
        for r in utente.recensioni_ricevute
    ]

    messaggi = db.scalars(
        select(Messaggio).where(Messaggio.mittente_id == utente.id)
        .order_by(Messaggio.creato_il)
    ).all()
    dati["messaggi_inviati"] = [
        {"conversazione_id": m.conversazione_id, "testo": m.testo,
         "creato_il": m.creato_il.isoformat()}
        for m in messaggi
    ]
    # Solo i propri: i messaggi ricevuti sono dati di chi li ha scritti, e
    # regalarli in un file scaricabile non sarebbe corretto verso di loro.

    dati["utenti_bloccati"] = [
        {"nome": b.bloccato.nome_visualizzato, "motivo": b.motivo}
        for b in utente.blocchi_effettuati
    ]
    return dati


# --- Diritto alla cancellazione --------------------------------------------
def _svuota_profilo(db: Session, utente: Utente) -> None:
    """Elimina il profilo e le foto, sia dal database sia dal disco."""
    bagnino = utente.profilo_bagnino
    if bagnino is not None:
        elimina_immagine(bagnino.foto)
        # `delete-orphan` porta via brevetti, esperienze, disponibilità e i
        # collegamenti alle zone.
        db.delete(bagnino)

    piscina = utente.profilo_piscina
    if piscina is not None:
        for foto in db.scalars(
            select(FotoPiscina).where(FotoPiscina.piscina_id == piscina.id)
        ).all():
            elimina_immagine(foto.percorso)
        db.delete(piscina)


def cancella(db: Session, utente: Utente) -> Utente:
    """Cancella i dati personali, lasciando in piedi ciò che riguarda gli altri.

    Non è reversibile: dopo, non c'è più nessun dato con cui ricostruire chi
    fosse questa persona.
    """
    _svuota_profilo(db, utente)

    # Gli annunci ancora aperti spariscono: nessuno deve rispondere a un turno
    # di un account che non esiste più. Quelli già assegnati o chiusi restano —
    # sono la storia lavorativa anche della controparte — ma senza più un nome
    # attaccato.
    for annuncio in list(utente.annunci):
        if annuncio.stato in (StatoAnnuncio.BOZZA, StatoAnnuncio.APERTO):
            db.delete(annuncio)

    # Le candidature ancora in ballo si ritirano da sole.
    for candidatura in list(utente.candidature):
        db.delete(candidatura)

    # I blocchi non servono più a nessuno dei due.
    for blocco in list(utente.blocchi_effettuati) + list(utente.blocchi_subiti):
        db.delete(blocco)

    # I codici via email valgono solo per questo account.
    for token in list(utente.token_email):
        db.delete(token)

    # Le conversazioni restano all'altra persona, ma questo account esce
    # dall'elenco dei partecipanti: non deve più ricevere niente.
    for partecipazione in list(utente.partecipazioni):
        db.delete(partecipazione)

    # I dati identificativi. L'indirizzo diventa uno di un dominio riservato,
    # ma resta *unico*: la colonna ha un vincolo di unicità, e due cancellazioni
    # con lo stesso indirizzo si rifiuterebbero a vicenda.
    utente.email = f"cancellato-{utente.id}@{DOMINIO_ANONIMO}"
    utente.telefono = None
    # Senza hash nessuna password può funzionare: `verify_password` fallisce e
    # l'account non è più raggiungibile nemmeno col recupero.
    utente.password_hash = None
    utente.telefono_pubblico = False
    utente.email_verificata = False
    utente.verificato = False
    utente.attivo = False
    utente.cancellato_il = utcnow()

    db.commit()
    db.refresh(utente)
    return utente


def riepilogo(utente: Utente) -> dict:
    """Cosa succederà, da mostrare prima di far premere il pulsante.

    Chi cancella ha diritto di sapere che alcune cose restano, e perché.
    """
    aperti = sum(
        1 for a in utente.annunci
        if a.stato in (StatoAnnuncio.BOZZA, StatoAnnuncio.APERTO)
    )
    storici = len(utente.annunci) - aperti
    return {
        "profilo": bool(utente.profilo),
        "annunci_da_eliminare": aperti,
        "annunci_che_restano": storici,
        "candidature_da_eliminare": len(utente.candidature),
        "recensioni_scritte_che_restano": len(utente.recensioni_scritte),
        "recensioni_ricevute_che_restano": len(utente.recensioni_ricevute),
        "conversazioni": len(utente.partecipazioni),
    }
