"""Registro delle azioni fatte dallo staff sugli account altrui."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import TipoAzioneStaff, enum_col

if TYPE_CHECKING:
    from app.models.utente import Utente


class AzioneStaff(TimestampMixin, Base):
    """Chi ha fatto cosa, a chi e perché.

    Sospendere un account o togliere la verifica a un brevetto sono decisioni
    che vanno spiegate se qualcuno le contesta. Senza registro resta solo la
    parola dello staff contro quella dell'utente.

    Il collegamento allo staff è `SET NULL`: se un giorno quell'account viene
    cancellato la riga resta, con la sua email conservata a parte.
    """

    __tablename__ = "azioni_staff"

    id: Mapped[int] = mapped_column(primary_key=True)

    staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("utenti.id", ondelete="SET NULL"), index=True
    )
    # Copia dell'email al momento dell'azione: sopravvive alla cancellazione.
    staff_email: Mapped[str] = mapped_column(String(255), nullable=False)

    azione: Mapped[TipoAzioneStaff] = mapped_column(
        enum_col(TipoAzioneStaff), nullable=False, index=True
    )
    # A cosa si riferisce: "utente" o "brevetto", più il suo id.
    oggetto_tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    oggetto_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # Descrizione leggibile dell'oggetto, così il registro si legge da solo.
    oggetto_etichetta: Mapped[str | None] = mapped_column(String(255))

    motivo: Mapped[str | None] = mapped_column(String(500))

    staff: Mapped[Utente | None] = relationship(foreign_keys=[staff_id])

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<AzioneStaff {self.azione} {self.oggetto_tipo}={self.oggetto_id}>"
