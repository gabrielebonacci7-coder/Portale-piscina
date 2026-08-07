"""Profilo della struttura che pubblica annunci."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import TipoStruttura, enum_col

if TYPE_CHECKING:
    from app.models.annuncio import Annuncio
    from app.models.bagnino import Esperienza
    from app.models.utente import Utente
    from app.models.zona import Zona


class ProfiloPiscina(TimestampMixin, Base):
    """Piscina / struttura natatoria, con i dati del referente che pubblica."""

    __tablename__ = "profili_piscina"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    nome_struttura: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    tipo_struttura: Mapped[TipoStruttura] = mapped_column(
        enum_col(TipoStruttura), default=TipoStruttura.ALTRO, nullable=False, index=True
    )

    citta: Mapped[str] = mapped_column(String(80), default="Roma", nullable=False, index=True)
    zona_id: Mapped[int | None] = mapped_column(
        ForeignKey("zone.id", ondelete="SET NULL"), index=True
    )
    indirizzo: Mapped[str | None] = mapped_column(String(200))

    partita_iva: Mapped[str | None] = mapped_column(String(20))
    numero_vasche: Mapped[int | None] = mapped_column(Integer)
    descrizione: Mapped[str | None] = mapped_column(Text)

    # Chi pubblica gli annunci per la struttura.
    referente_nome: Mapped[str | None] = mapped_column(String(120))
    referente_ruolo: Mapped[str | None] = mapped_column(String(80))  # gestore, direttore, HR...
    referente_telefono: Mapped[str | None] = mapped_column(String(32))
    referente_email: Mapped[str | None] = mapped_column(String(255))

    attiva: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    utente: Mapped[Utente] = relationship(back_populates="profilo_piscina")
    zona: Mapped[Zona | None] = relationship()
    annunci: Mapped[list[Annuncio]] = relationship(back_populates="piscina")
    esperienze_collegate: Mapped[list[Esperienza]] = relationship(back_populates="piscina")

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<ProfiloPiscina {self.id} {self.nome_struttura}>"
