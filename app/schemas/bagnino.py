from datetime import date, time

from pydantic import BaseModel, Field, model_validator

from app.models.enums import TipoBrevetto
from app.schemas.common import ORMModel
from app.schemas.zona import ZonaRead


# --- Brevetto -------------------------------------------------------------
class BrevettoBase(BaseModel):
    tipo: TipoBrevetto
    ente: str = "FIN"
    numero: str | None = Field(default=None, max_length=64)
    data_rilascio: date | None = None
    data_scadenza: date | None = None

    @model_validator(mode="after")
    def _scadenza_dopo_rilascio(self):
        if self.data_rilascio and self.data_scadenza and self.data_scadenza < self.data_rilascio:
            raise ValueError("la data di scadenza precede quella di rilascio")
        return self


class BrevettoCreate(BrevettoBase):
    pass


class BrevettoRead(ORMModel, BrevettoBase):
    id: int
    verificato: bool
    # Proprietà calcolate sul modello ORM, non colonne.
    valido: bool
    giorni_alla_scadenza: int | None = None


# --- Esperienza -----------------------------------------------------------
class EsperienzaBase(BaseModel):
    struttura: str = Field(max_length=150)
    piscina_id: int | None = None
    zona: str | None = Field(default=None, max_length=80)
    mansione: str | None = Field(default=None, max_length=120)
    data_inizio: date | None = None
    data_fine: date | None = None
    stagioni: int | None = Field(default=None, ge=0, le=60)
    descrizione: str | None = None


class EsperienzaCreate(EsperienzaBase):
    pass


class EsperienzaRead(ORMModel, EsperienzaBase):
    id: int
    in_corso: bool


# --- Disponibilità --------------------------------------------------------
class DisponibilitaBase(BaseModel):
    giorno_settimana: int = Field(ge=0, le=6, description="0 = lunedì ... 6 = domenica")
    ora_inizio: time
    ora_fine: time
    note: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _fascia_valida(self):
        if self.ora_fine <= self.ora_inizio:
            raise ValueError("ora_fine deve essere successiva a ora_inizio")
        return self


class DisponibilitaCreate(DisponibilitaBase):
    pass


class DisponibilitaRead(ORMModel, DisponibilitaBase):
    id: int


# --- Profilo bagnino ------------------------------------------------------
class ProfiloBagninoBase(BaseModel):
    nome: str = Field(max_length=80)
    cognome: str = Field(max_length=80)
    data_nascita: date | None = None
    citta: str = "Roma"
    note_spostamenti: str | None = Field(default=None, max_length=255)
    anni_esperienza: int = Field(default=0, ge=0, le=60)
    bio: str | None = None
    disponibile_chiamata_singola: bool = True
    cerca_lavoro: bool = True


class ProfiloBagninoCreate(ProfiloBagninoBase):
    # `utente_id` non si passa: viene dal token di chi sta chiamando.
    zone_ids: list[int] = Field(default_factory=list)


class ProfiloBagninoUpdate(BaseModel):
    """Aggiornamento parziale: si inviano solo i campi da cambiare."""

    nome: str | None = Field(default=None, max_length=80)
    cognome: str | None = Field(default=None, max_length=80)
    data_nascita: date | None = None
    citta: str | None = None
    note_spostamenti: str | None = Field(default=None, max_length=255)
    anni_esperienza: int | None = Field(default=None, ge=0, le=60)
    bio: str | None = None
    disponibile_chiamata_singola: bool | None = None
    cerca_lavoro: bool | None = None
    zone_ids: list[int] | None = None


class ProfiloBagninoRead(ORMModel, ProfiloBagninoBase):
    id: int
    utente_id: int
    eta: int | None = None
    abilitato: bool
    zone: list[ZonaRead] = Field(default_factory=list)
    brevetti: list[BrevettoRead] = Field(default_factory=list)
    esperienze: list[EsperienzaRead] = Field(default_factory=list)
    disponibilita: list[DisponibilitaRead] = Field(default_factory=list)


class ProfiloBagninoSintesi(ORMModel):
    """Versione leggera per gli elenchi della bacheca."""

    id: int
    utente_id: int
    nome: str
    cognome: str
    citta: str
    eta: int | None = None
    anni_esperienza: int
    abilitato: bool
    disponibile_chiamata_singola: bool
    zone: list[ZonaRead] = Field(default_factory=list)
