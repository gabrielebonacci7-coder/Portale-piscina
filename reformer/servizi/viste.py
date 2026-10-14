"""Come le lezioni e le clienti si presentano all'app.

Due versioni della stessa lezione: quella per la cliente dice quanti posti
restano e com'è messa lei, **mai chi c'è iscritto**; quella per lo staff ha
i nomi, le presenze e la lista d'attesa.
"""

from reformer.core.config import settings
from reformer.dominio import orario
from reformer.models import Lezione, Utente
from reformer.servizi.regole import disdicibile, fine_lezione, limite_disdetta

def _base(lez: Lezione) -> dict:
    ist = orario.ISTRUTTRICI[lez.istruttrice]
    return {
        "id": lez.id,
        "inizio": lez.inizio.isoformat(),
        "fine": fine_lezione(lez).isoformat(),
        "istruttrice": {"id": ist["id"], "nome": ist["nome"], "cognome": ist["cognome"]},
        "titolo": lez.titolo,
        "posti": lez.posti,
        "occupati": len(lez.attive),
        "liberi": lez.liberi,
        "annullata": lez.annullata_il is not None,
        "motivo_annullamento": lez.motivo_annullamento,
        "passata": lez.inizio <= orario.adesso(),
        "disdicibile": disdicibile(lez),
        "limite_disdetta": limite_disdetta(lez).isoformat(),
        "prenotabile": orario.locale(lez.inizio).date() <= orario.ultimo_giorno_prenotabile(),
    }

def per_cliente(lez: Lezione, utente: Utente) -> dict:
    d = _base(lez)
    mia = next((p for p in lez.attive if p.utente_id == utente.id), None)
    attesa = [a.utente_id for a in lez.attese]
    d["mia"] = mia is not None
    d["presente"] = mia.presente if mia else None
    d["in_attesa"] = attesa.index(utente.id) + 1 if utente.id in attesa else None
    d["attesa_quante"] = len(attesa)
    return d

def per_staff(lez: Lezione) -> dict:
    d = _base(lez)
    d["iscritte"] = [
        {
            "id": p.utente_id,
            "nome": p.utente.nome_completo,
            "presente": p.presente,
            "lezioni_rimaste": p.utente.lezioni_rimaste,
            "dalla_lista": p.dalla_lista,
        }
        for p in sorted(lez.attive, key=lambda x: x.creato_il)
    ]
    d["attesa"] = [{"id": a.utente_id, "nome": a.utente.nome_completo} for a in lez.attese]
    return d

def utente(u: Utente) -> dict:
    return {
        "id": u.id,
        "nome": u.nome,
        "cognome": u.cognome,
        "email": u.email,
        "telefono": u.telefono,
        "ruolo": u.ruolo.value,
        "email_confermata": u.email_verificata_il is not None,
        "lezioni_rimaste": u.lezioni_rimaste,
        "scadenza": u.scadenza.isoformat() if u.scadenza else None,
        "iscritta_il": u.creato_il.isoformat(),
    }

def regole() -> dict:
    return {
        "posti": settings.posti_per_lezione,
        "ore_disdetta": settings.ore_disdetta,
        "giorni_prenotabili": settings.giorni_prenotabili,
    }
