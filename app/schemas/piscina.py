from pydantic import BaseModel, EmailStr, Field

from app.models.enums import TipoStruttura
from app.schemas.common import ORMModel
from app.schemas.zona import ZonaRead


class ProfiloPiscinaBase(BaseModel):
    nome_struttura: str = Field(max_length=150)
    tipo_struttura: TipoStruttura = TipoStruttura.ALTRO
    citta: str = "Roma"
    zona_id: int | None = None
    indirizzo: str | None = Field(default=None, max_length=200)
    partita_iva: str | None = Field(default=None, max_length=20)
    numero_vasche: int | None = Field(default=None, ge=1)
    descrizione: str | None = None

    referente_nome: str | None = Field(default=None, max_length=120)
    referente_ruolo: str | None = Field(default=None, max_length=80)
    referente_telefono: str | None = Field(default=None, max_length=32)
    referente_email: EmailStr | None = None


class ProfiloPiscinaCreate(ProfiloPiscinaBase):
    utente_id: int


class ProfiloPiscinaRead(ORMModel, ProfiloPiscinaBase):
    id: int
    utente_id: int
    attiva: bool
    zona: ZonaRead | None = None
