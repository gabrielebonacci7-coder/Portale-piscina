"""Accesso allo staff e viste del gestionale."""

from pydantic import BaseModel, EmailStr, Field


class AccessoIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class TokenOut(BaseModel):
    token: str
    nome: str
    email: str


class CambioStatoIn(BaseModel):
    stato: str


class PostazioneStaffIn(BaseModel):
    attiva: bool | None = None
    nota: str | None = Field(default=None, max_length=120)
