from pydantic import BaseModel, EmailStr, Field

from app.models.enums import TipoUtente
from app.schemas.utente import UtenteRead


class Token(BaseModel):
    """Risposta del login, nel formato atteso dallo standard OAuth2."""

    access_token: str
    token_type: str = "bearer"
    utente: UtenteRead


class LoginRequest(BaseModel):
    """Login in JSON, alternativa al form OAuth2 (comodo dal frontend)."""

    email: EmailStr
    password: str


class RegistrazioneRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    tipo: TipoUtente
    telefono: str | None = Field(default=None, max_length=32)
    telefono_pubblico: bool = False


class RichiestaRecupero(BaseModel):
    email: EmailStr


class ReimpostaPassword(BaseModel):
    codice: str = Field(min_length=8, max_length=128)
    password_nuova: str = Field(min_length=8, max_length=72)


class ConfermaEmail(BaseModel):
    codice: str = Field(min_length=8, max_length=128)


class CambioPassword(BaseModel):
    password_attuale: str
    password_nuova: str = Field(min_length=8, max_length=72)
