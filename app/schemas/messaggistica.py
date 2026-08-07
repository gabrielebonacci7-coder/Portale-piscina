from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TipoUtente
from app.schemas.common import ORMModel


class InterlocutoreSintesi(ORMModel):
    """Con chi si sta parlando."""

    id: int
    tipo: TipoUtente
    nome_visualizzato: str


class MessaggioCreate(BaseModel):
    testo: str = Field(min_length=1, max_length=4000)

    @field_validator("testo")
    @classmethod
    def _non_solo_spazi(cls, v: str) -> str:
        pulito = v.strip()
        if not pulito:
            raise ValueError("il messaggio non può essere vuoto")
        return pulito


class MessaggioRead(ORMModel):
    id: int
    conversazione_id: int
    mittente_id: int
    testo: str
    creato_il: datetime


class ConversazioneAvvia(MessaggioCreate):
    """Apre una conversazione (o riusa quella esistente) e invia il primo messaggio."""

    destinatario_id: int
    annuncio_id: int | None = None


class ConversazioneRead(BaseModel):
    id: int
    annuncio_id: int | None = None
    interlocutore: InterlocutoreSintesi | None = None
    ultimo_messaggio: str | None = None
    ultimo_messaggio_il: datetime | None = None
    non_letti: int = 0


class BloccoCreate(BaseModel):
    motivo: str | None = Field(default=None, max_length=255)


class BloccoRead(ORMModel):
    id: int
    bloccato_id: int
    motivo: str | None = None
    creato_il: datetime
