"""Contenitore per le risposte paginate."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    """Elenco + conteggio totale, così il frontend sa quante pagine mostrare."""

    totale: int
    skip: int
    limit: int
    elementi: list[T]
