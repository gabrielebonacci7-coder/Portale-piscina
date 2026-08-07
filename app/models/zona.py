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
    # Il quartiere ("EUR") o il comune ("Frascati").
    nome: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    # Il comune vero: "Roma" per i quartieri romani, il comune stesso per i
    # paesi fuori Roma. Serve perché "Frascati" non è Roma e non va detto che lo sia.
    citta: Mapped[str] = mapped_column(String(80), nullable=False, default="Roma", index=True)
    # Il raggruppamento con cui la zona si sceglie nell'app: "Roma",
    # "Castelli Romani", e in futuro "Litorale", "Tivoli e dintorni"...
    area: Mapped[str] = mapped_column(String(80), nullable=False, default="Roma", index=True)
    # Sotto-etichetta, usata dove ha senso: a Roma è il municipio.
    macro_area: Mapped[str | None] = mapped_column(String(80))

    bagnini: Mapped[list[ProfiloBagnino]] = relationship(
        secondary=bagnino_zone, back_populates="zone"
    )

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Zona {self.citta}/{self.nome}>"
