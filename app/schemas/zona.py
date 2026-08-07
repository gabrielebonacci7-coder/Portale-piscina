from app.schemas.common import ORMModel


class ZonaRead(ORMModel):
    id: int
    nome: str
    citta: str
    # Raggruppamento con cui la zona si sceglie nell'app.
    area: str = "Roma"
    macro_area: str | None = None
