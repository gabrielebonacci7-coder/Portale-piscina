from app.schemas.common import ORMModel


class ZonaRead(ORMModel):
    id: int
    nome: str
    citta: str
    macro_area: str | None = None
