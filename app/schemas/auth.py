from pydantic import BaseModel, EmailStr, Field, field_validator

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
    # Senza default: chi si iscrive deve dire di sì esplicitamente. Una casella
    # già spuntata non è un consenso, e nemmeno un campo che si può omettere.
    accetta_privacy: bool

    @field_validator("accetta_privacy")
    @classmethod
    def deve_accettare(cls, valore: bool) -> bool:
        if not valore:
            raise ValueError("Per iscriverti devi accettare l'informativa privacy")
        return valore


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


class CancellaAccount(BaseModel):
    """La password serve: cancellare è irreversibile, e un telefono lasciato
    sbloccato sul tavolo non deve bastare a distruggere un account."""

    password: str
    # Da scrivere a mano: un secondo gesto consapevole, non un altro "ok".
    conferma: str = Field(description="Scrivere CANCELLA")
