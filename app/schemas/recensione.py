from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

Voto = Field(default=None, ge=1, le=5)


class RecensioneBase(BaseModel):
    destinatario_id: int
    annuncio_id: int | None = None
    stelle: int = Field(ge=1, le=5)
    commento: str | None = Field(default=None, max_length=2000)

    voto_puntualita: int | None = Voto
    voto_professionalita: int | None = Voto
    voto_ambiente: int | None = Voto
    voto_pagamento: int | None = Voto


class RecensioneCreate(RecensioneBase):
    """`autore_id` non si passa: viene dal token di chi sta recensendo."""


class RecensioneRead(ORMModel, RecensioneBase):
    id: int
    autore_id: int
    autore_nome: str | None = None
    creato_il: datetime


class RiepilogoRecensioni(BaseModel):
    """Media e conteggi mostrati sul profilo."""

    destinatario_id: int
    totale: int
    media_stelle: float | None = None
    media_puntualita: float | None = None
    media_professionalita: float | None = None
    media_ambiente: float | None = None
    media_pagamento: float | None = None
    recensioni: list[RecensioneRead] = Field(default_factory=list)
