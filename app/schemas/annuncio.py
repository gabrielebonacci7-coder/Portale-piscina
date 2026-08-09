from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    StatoAnnuncio,
    TipoAnnuncio,
    TipoBrevetto,
    TipoCompenso,
    TipoTurno,
    TipoUtente,
)
from app.schemas.common import ORMModel
from app.schemas.zona import ZonaRead


class AnnuncioBase(BaseModel):
    titolo: str = Field(max_length=150)
    tipo: TipoAnnuncio
    piscina_id: int | None = None

    data_inizio: datetime
    data_fine: datetime | None = None

    citta: str = "Roma"
    zona_id: int | None = None
    indirizzo: str | None = Field(default=None, max_length=200)

    compenso: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    compenso_tipo: TipoCompenso = TipoCompenso.ORARIO
    valuta: str = Field(default="EUR", min_length=3, max_length=3)

    tipo_turno: TipoTurno = TipoTurno.TURNO_FISSO
    brevetto_richiesto: TipoBrevetto | None = None
    urgente: bool = False
    note: str | None = None

    @model_validator(mode="after")
    def _date_coerenti(self):
        if self.data_fine and self.data_fine < self.data_inizio:
            raise ValueError("data_fine precede data_inizio")
        return self


class AnnuncioCreate(AnnuncioBase):
    """`autore_id` non si passa: viene dal token di chi sta pubblicando."""


class AnnuncioUpdate(BaseModel):
    """Aggiornamento parziale: si inviano solo i campi da cambiare."""

    titolo: str | None = Field(default=None, max_length=150)
    data_inizio: datetime | None = None
    data_fine: datetime | None = None
    zona_id: int | None = None
    indirizzo: str | None = None
    compenso: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    compenso_tipo: TipoCompenso | None = None
    tipo_turno: TipoTurno | None = None
    brevetto_richiesto: TipoBrevetto | None = None
    urgente: bool | None = None
    note: str | None = None
    # `assegnato_a_id` non si cambia da qui: si usa POST /annunci/{id}/assegna.
    stato: StatoAnnuncio | None = None


class AutoreSintesi(ORMModel):
    """Chi ha pubblicato, in breve, per le schede della bacheca."""

    id: int
    tipo: TipoUtente
    nome_visualizzato: str


class AnnuncioRead(ORMModel, AnnuncioBase):
    id: int
    autore_id: int
    stato: StatoAnnuncio
    assegnato_a_id: int | None = None
    zona: ZonaRead | None = None
    autore: AutoreSintesi | None = None
    # Chi copre il turno: serve alla struttura per sapere chi aspettarsi, e
    # a entrambi per sapere chi recensire a turno concluso.
    assegnato_a: AutoreSintesi | None = None
    creato_il: datetime
