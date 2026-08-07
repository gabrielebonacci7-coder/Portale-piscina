"""Chat interna: conversazioni a due, messaggi, e blocco di un utente."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.db.types import UTCDateTime

if TYPE_CHECKING:
    from app.models.annuncio import Annuncio
    from app.models.utente import Utente


class Conversazione(TimestampMixin, Base):
    """Una conversazione fra due utenti.

    Vale per qualsiasi coppia — piscina/bagnino ma anche bagnino/bagnino, che
    fra colleghi si scambiano turni. La tabella dei partecipanti tiene lo stato
    di lettura di ciascuno e lascia aperta la porta a gruppi in futuro.
    """

    __tablename__ = "conversazioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Da quale annuncio è nata: solo contesto, impostato alla creazione.
    # Fra due persone resta comunque una conversazione sola.
    annuncio_id: Mapped[int | None] = mapped_column(
        ForeignKey("annunci.id", ondelete="SET NULL"), index=True
    )
    # Data dell'ultimo messaggio: serve a ordinare l'elenco senza join.
    ultimo_messaggio_il: Mapped[datetime | None] = mapped_column(UTCDateTime, index=True)

    annuncio: Mapped[Annuncio | None] = relationship()
    partecipanti: Mapped[list[Partecipante]] = relationship(
        back_populates="conversazione", cascade="all, delete-orphan"
    )
    messaggi: Mapped[list[Messaggio]] = relationship(
        back_populates="conversazione",
        cascade="all, delete-orphan",
        order_by="Messaggio.creato_il",
    )

    def altro_partecipante(self, utente_id: int) -> Partecipante | None:
        """L'interlocutore, dal punto di vista di `utente_id`."""
        for p in self.partecipanti:
            if p.utente_id != utente_id:
                return p
        return None

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Conversazione {self.id}>"


class Partecipante(Base):
    """Chi fa parte di una conversazione, e fin dove ha letto."""

    __tablename__ = "partecipanti_conversazione"
    __table_args__ = (
        UniqueConstraint("conversazione_id", "utente_id", name="uq_partecipante"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversazione_id: Mapped[int] = mapped_column(
        ForeignKey("conversazioni.id", ondelete="CASCADE"), nullable=False, index=True
    )
    utente_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # None = non ha mai aperto la conversazione.
    ultimo_letto_il: Mapped[datetime | None] = mapped_column(UTCDateTime)

    conversazione: Mapped[Conversazione] = relationship(back_populates="partecipanti")
    utente: Mapped[Utente] = relationship(back_populates="partecipazioni")

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Partecipante utente={self.utente_id} conv={self.conversazione_id}>"


class Messaggio(Base):
    """Un messaggio dentro una conversazione."""

    __tablename__ = "messaggi"
    __table_args__ = (
        CheckConstraint("length(trim(testo)) > 0", name="ck_messaggio_non_vuoto"),
        CheckConstraint("length(testo) <= 4000", name="ck_messaggio_lunghezza"),
        # L'elenco dei messaggi si legge sempre per conversazione e in ordine.
        Index("ix_messaggi_conv_data", "conversazione_id", "creato_il"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversazione_id: Mapped[int] = mapped_column(
        ForeignKey("conversazioni.id", ondelete="CASCADE"), nullable=False
    )
    mittente_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    testo: Mapped[str] = mapped_column(Text, nullable=False)
    creato_il: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, index=True)

    conversazione: Mapped[Conversazione] = relationship(back_populates="messaggi")
    mittente: Mapped[Utente] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Messaggio {self.id} da {self.mittente_id}>"


class Blocco(TimestampMixin, Base):
    """Un utente ha bloccato un altro: niente più messaggi fra i due.

    Serve perché la chat è aperta a chiunque sia iscritto. Senza una via
    d'uscita, una piattaforma dove sconosciuti si scrivono non è accettabile.
    """

    __tablename__ = "blocchi"
    __table_args__ = (
        UniqueConstraint("bloccante_id", "bloccato_id", name="uq_blocco"),
        CheckConstraint("bloccante_id <> bloccato_id", name="ck_blocco_non_se_stesso"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bloccante_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bloccato_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    motivo: Mapped[str | None] = mapped_column(String(255))

    bloccante: Mapped[Utente] = relationship(
        foreign_keys=[bloccante_id], back_populates="blocchi_effettuati"
    )
    bloccato: Mapped[Utente] = relationship(
        foreign_keys=[bloccato_id], back_populates="blocchi_subiti"
    )

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Blocco {self.bloccante_id} -x-> {self.bloccato_id}>"
