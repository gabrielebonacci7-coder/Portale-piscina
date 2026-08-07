from datetime import datetime

from pydantic import BaseModel, Field, model_validator

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
    autore_id: int

    @model_validator(mode="after")
    def _no_autorecensione(self):
        if self.autore_id == self.destinatario_id:
            raise ValueError("non si può recensire se stessi")
        return self


class RecensioneRead(ORMModel, RecensioneBase):
    id: int
    autore_id: int
    creato_il: datetime
