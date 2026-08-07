"""Zone geografiche (municipi / quartieri) usate per filtrare gli annunci."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.bagnino import ProfiloBagnino

# Un bagnino può coprire più zone, una zona ha più bagnini: many-to-many.
bagnino_zone = Table(
    "bagnino_zone",
    Base.metadata,
    Column("bagnino_id", ForeignKey("profili_bagnino.id", ondelete="CASCADE"), primary_key=True),
    Column("zona_id", ForeignKey("zone.id", ondelete="CASCADE"), primary_key=True),
)


class Zona(Base):
    """Zona operativa. Tabella di lookup, popolata dal seed iniziale."""

    __tablename__ = "zone"
    __table_args__ = (UniqueConstraint("citta", "nome", name="uq_zona_citta_nome"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    citta: Mapped[str] = mapped_column(String(80), nullable=False, default="Roma", index=True)
    # Es. "Municipio II"; utile a Roma per raggruppare i quartieri.
    macro_area: Mapped[str | None] = mapped_column(String(80))

    bagnini: Mapped[list[ProfiloBagnino]] = relationship(
        secondary=bagnino_zone, back_populates="zone"
    )

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Zona {self.citta}/{self.nome}>"
