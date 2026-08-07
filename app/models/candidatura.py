"""Candidature: la risposta di un utente a un annuncio."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import StatoCandidatura, enum_col

if TYPE_CHECKING:
    from app.models.annuncio import Annuncio
    from app.models.utente import Utente


class Candidatura(TimestampMixin, Base):
    """Un utente si propone per un turno pubblicato da qualcun altro.

    È il pezzo che rende la bacheca bidirezionale: senza, chi pubblica
    dovrebbe già sapere a chi assegnare il turno.
    """

    __tablename__ = "candidature"
    __table_args__ = (
        # Ci si candida una volta sola per annuncio.
        UniqueConstraint("annuncio_id", "candidato_id", name="uq_candidatura"),
        CheckConstraint("messaggio IS NULL OR length(messaggio) <= 1000", name="ck_candidatura_msg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    annuncio_id: Mapped[int] = mapped_column(
        ForeignKey("annunci.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidato_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )

    messaggio: Mapped[str | None] = mapped_column(Text)
    stato: Mapped[StatoCandidatura] = mapped_column(
        enum_col(StatoCandidatura), default=StatoCandidatura.INVIATA, nullable=False, index=True
    )

    annuncio: Mapped[Annuncio] = relationship(back_populates="candidature")
    candidato: Mapped[Utente] = relationship(back_populates="candidature")

    @property
    def modificabile(self) -> bool:
        """Ci si ritira solo finché la candidatura è ancora in attesa."""
        return self.stato == StatoCandidatura.INVIATA

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Candidatura {self.candidato_id} -> annuncio {self.annuncio_id} ({self.stato})>"
