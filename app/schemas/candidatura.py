from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import StatoCandidatura, TipoUtente
from app.schemas.common import ORMModel


class CandidaturaCreate(BaseModel):
    """`annuncio_id` sta nel percorso, `candidato_id` viene dal token."""

    messaggio: str | None = Field(default=None, max_length=1000)


class CandidatoSintesi(ORMModel):
    """Chi si è candidato, in breve: quanto basta per decidere senza aprire il profilo."""

    id: int
    tipo: TipoUtente
    nome_visualizzato: str


class CandidaturaRead(ORMModel):
    id: int
    annuncio_id: int
    candidato_id: int
    messaggio: str | None = None
    stato: StatoCandidatura
    creato_il: datetime
    candidato: CandidatoSintesi | None = None


class CandidaturaConAnnuncio(CandidaturaRead):
    """Usato in "le mie candidature": serve sapere a cosa ci si è candidati."""

    annuncio_titolo: str | None = None
    annuncio_data_inizio: datetime | None = None
