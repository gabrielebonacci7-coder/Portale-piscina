"""Chi entra nel gestionale: bagnini, cassa, direzione."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from piscina.db.base import Base, TimestampMixin


class Operatore(Base, TimestampMixin):
    """Un account dello staff.

    Non c'è registrazione: gli account li crea la direzione da riga di comando
    (`python -m piscina.scripts.crea_operatore`). È l'unica porta d'ingresso ai
    dati personali di chi prenota, e non deve poterla aprire chi passa di lì.
    """

    __tablename__ = "operatori"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(120))
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Operatore {self.email}>"
