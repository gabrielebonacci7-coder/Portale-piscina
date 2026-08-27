"""Come entrano ed escono i dati delle prenotazioni."""

from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from piscina.dominio.disponibilita import ETICHETTE, FASCE, orario_esteso
from piscina.dominio.listino import euro


class SceltaIn(BaseModel):
    """Una postazione presa dalla mappa."""

    codice: str = Field(min_length=1, max_length=8)
    lettini: int = Field(default=0, ge=0, le=3)


class PrenotazioneIn(BaseModel):
    giorno: date
    fascia: str
    postazioni: list[SceltaIn] = Field(min_length=1, max_length=10)

    nome: str = Field(min_length=2, max_length=80)
    telefono: str = Field(min_length=6, max_length=24)
    email: EmailStr
    persone: int = Field(default=1, ge=1, le=20)
    note: str = Field(default="", max_length=300)

    @field_validator("fascia")
    @classmethod
    def _fascia_valida(cls, v: str) -> str:
        if v not in FASCE:
            raise ValueError(f"fascia sconosciuta: {v}")
        return v

    @field_validator("telefono")
    @classmethod
    def _telefono_plausibile(cls, v: str) -> str:
        cifre = "".join(c for c in v if c.isdigit())
        if len(cifre) < 8:
            raise ValueError("il numero di telefono sembra incompleto")
        return v.strip()

    @field_validator("nome")
    @classmethod
    def _nome_pulito(cls, v: str) -> str:
        return " ".join(v.split())


class RigaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codice: str
    tipo: str
    lettini: int
    prezzo_cent: int
    prezzo: str


class PrenotazioneOut(BaseModel):
    codice: str
    giorno: date
    fascia: str
    fascia_etichetta: str
    orario: str
    stato: str
    persone: int
    note: str
    nome: str
    telefono: str
    email: str
    totale_cent: int
    totale: str
    righe: list[RigaOut]

    @classmethod
    def da_modello(cls, p) -> "PrenotazioneOut":
        return cls(
            codice=p.codice,
            giorno=p.giorno,
            fascia=p.fascia,
            fascia_etichetta=ETICHETTE[p.fascia],
            orario=orario_esteso(p.fascia),
            stato=p.stato,
            persone=p.persone,
            note=p.note,
            nome=p.nome,
            telefono=p.telefono,
            email=p.email,
            totale_cent=p.totale_cent,
            totale=euro(p.totale_cent),
            righe=[
                RigaOut(
                    codice=r.postazione.codice,
                    tipo=r.postazione.tipo,
                    lettini=r.lettini,
                    prezzo_cent=r.prezzo_cent,
                    prezzo=euro(r.prezzo_cent),
                )
                for r in sorted(p.righe, key=lambda r: r.postazione.codice)
            ],
        )


class AnnullaIn(BaseModel):
    telefono: str = Field(min_length=6, max_length=24)


class PostazioneOut(BaseModel):
    codice: str
    tipo: str
    fila: str
    x: float
    y: float
    max_lettini: int
    attiva: bool
    nota: str
    libera_mattina: bool
    libera_pomeriggio: bool


class MappaOut(BaseModel):
    giorno: date
    viewbox: str
    lettini_disegnati: int
    postazioni: list[PostazioneOut]
    scenografia: list[dict]
    rotazioni: dict[str, int]
    riepilogo: dict
