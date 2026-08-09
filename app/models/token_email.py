"""Token monouso spediti per email: verifica indirizzo e recupero password."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.db.types import UTCDateTime
from app.models.enums import TipoToken, enum_col

if TYPE_CHECKING:
    from app.models.utente import Utente


class TokenEmail(TimestampMixin, Base):
    """Un codice usa e getta mandato per email.

    Nel database ci finisce **l'impronta**, non il codice: chi leggesse una
    copia del database non deve poter entrare negli account altrui, esattamente
    come per le password.
    """

    __tablename__ = "token_email"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoToken] = mapped_column(enum_col(TipoToken), nullable=False, index=True)

    # SHA-256 del codice. È lungo e casuale, quindi non serve un hash lento
    # come per le password: non si può indovinare a forza bruta.
    impronta: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    scade_il: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    usato_il: Mapped[datetime | None] = mapped_column(UTCDateTime)

    utente: Mapped[Utente] = relationship(back_populates="token_email")

    @property
    def valido(self) -> bool:
        """Un token vale una volta sola, e solo entro la scadenza."""
        return self.usato_il is None and self.scade_il > datetime.now(timezone.utc)

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<TokenEmail {self.tipo} utente={self.utente_id} valido={self.valido}>"
