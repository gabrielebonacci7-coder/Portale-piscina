from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Ruolo, TipoUtente
from app.schemas.common import ORMModel


class UtenteBase(BaseModel):
    email: EmailStr
    telefono: str | None = Field(default=None, max_length=32)
    tipo: TipoUtente
    telefono_pubblico: bool = False


class UtenteCreate(UtenteBase):
    # La password arriva in chiaro solo qui e viene subito trasformata in hash.
    password: str = Field(min_length=8, max_length=128)


class UtenteRead(ORMModel):
    """Nessun campo sensibile: `password_hash` non esce mai dall'API."""

    id: int
    email: EmailStr
    telefono: str | None = None
    tipo: TipoUtente
    # Serve al frontend per decidere se mostrare la scheda "Gestione".
    ruolo: Ruolo = Ruolo.UTENTE
    attivo: bool
    email_verificata: bool
    verificato: bool
    creato_il: datetime
    # Servono al profilo per mostrare quando è stata accettata l'informativa, e
    # per accorgersi che nel frattempo ne è uscita una versione nuova.
    privacy_accettata_il: datetime | None = None
    privacy_versione: str | None = None
