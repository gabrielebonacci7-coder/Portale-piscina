"""Le postazioni del solarium: ombrelloni e lettini singoli."""

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from piscina.db.base import Base, TimestampMixin


class Postazione(Base, TimestampMixin):
    """Un ombrellone (con i suoi lettini) o un lettino singolo del solarium.

    Le coordinate arrivano dalla piantina e servono solo a disegnare la vista
    dall'alto. Stanno in tabella, e non solo nel file, perché lo staff deve
    poter spegnere una postazione (ombrellone rotto) senza toccare il codice.
    """

    __tablename__ = "postazioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    codice: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    tipo: Mapped[str] = mapped_column(String(16))  # "ombrellone" | "lettino"
    fila: Mapped[str] = mapped_column(String(2))
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    max_lettini: Mapped[int] = mapped_column(Integer, default=0)

    # Spenta = non prenotabile e disegnata in grigio: manutenzione, ombrellone
    # rotto, zona chiusa per una festa.
    attiva: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    nota: Mapped[str] = mapped_column(String(120), default="")

    righe = relationship("RigaPrenotazione", back_populates="postazione")

    def __repr__(self) -> str:
        return f"<Postazione {self.codice}>"
