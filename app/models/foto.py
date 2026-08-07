"""Foto delle strutture."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.immagini import url_anteprima, url_foto
from app.db.base_class import Base, TimestampMixin
from app.models.enums import TipoFoto, enum_col

if TYPE_CHECKING:
    from app.models.piscina import ProfiloPiscina


class FotoPiscina(TimestampMixin, Base):
    """Una foto della struttura, con l'indicazione di cosa mostra."""

    __tablename__ = "foto_piscina"

    id: Mapped[int] = mapped_column(primary_key=True)
    piscina_id: Mapped[int] = mapped_column(
        ForeignKey("profili_piscina.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Percorso relativo dentro la cartella media, es. "piscine/aB3xY.jpg".
    # L'anteprima si ricava aggiungendo "-p" prima dell'estensione.
    percorso: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoFoto] = mapped_column(
        enum_col(TipoFoto), default=TipoFoto.ALTRO, nullable=False, index=True
    )
    didascalia: Mapped[str | None] = mapped_column(String(200))
    ordine: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    piscina: Mapped[ProfiloPiscina] = relationship(back_populates="foto")

    @property
    def url(self) -> str | None:
        return url_foto(self.percorso)

    @property
    def anteprima_url(self) -> str | None:
        return url_anteprima(self.percorso)

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<FotoPiscina {self.id} {self.tipo}>"
