"""Import centralizzato dei modelli.

Importare questo pacchetto registra tutte le tabelle su `Base.metadata`:
`create_all()` e le future migrazioni Alembic vedono così l'intero schema.
"""

from app.db.base_class import Base
from app.models.annuncio import Annuncio
from app.models.bagnino import Brevetto, Disponibilita, Esperienza, ProfiloBagnino
from app.models.candidatura import Candidatura
from app.models.enums import (
    StatoAnnuncio,
    StatoCandidatura,
    TipoAnnuncio,
    TipoBrevetto,
    TipoCompenso,
    TipoFoto,
    TipoStruttura,
    TipoTurno,
    TipoUtente,
    brevetto_copre,
)
from app.models.foto import FotoPiscina
from app.models.messaggistica import Blocco, Conversazione, Messaggio, Partecipante
from app.models.piscina import ProfiloPiscina
from app.models.recensione import Recensione
from app.models.utente import Utente
from app.models.zona import Zona, bagnino_zone

__all__ = [
    "Base",
    "Annuncio",
    "Blocco",
    "Brevetto",
    "Candidatura",
    "Conversazione",
    "Disponibilita",
    "Esperienza",
    "FotoPiscina",
    "Messaggio",
    "Partecipante",
    "ProfiloBagnino",
    "ProfiloPiscina",
    "Recensione",
    "Utente",
    "Zona",
    "bagnino_zone",
    "StatoAnnuncio",
    "StatoCandidatura",
    "TipoAnnuncio",
    "TipoBrevetto",
    "TipoCompenso",
    "TipoFoto",
    "TipoStruttura",
    "TipoTurno",
    "TipoUtente",
    "brevetto_copre",
]
