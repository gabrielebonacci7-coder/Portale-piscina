"""Recensioni incrociate: piscina -> bagnino e bagnino -> piscina."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.annuncio import Annuncio
    from app.models.utente import Utente


def _voto(nome: str) -> CheckConstraint:
    return CheckConstraint(f"{nome} IS NULL OR {nome} BETWEEN 1 AND 5", name=f"ck_recensione_{nome}")


class Recensione(TimestampMixin, Base):
    """Una recensione lasciata da un utente a un altro, di norma dopo un turno.

    Un'unica tabella per entrambe le direzioni: il verso si ricava dal tipo
    dell'autore. I voti di dettaglio sono opzionali e ognuno compila quelli
    che hanno senso per lui (una piscina non vota "pagamento puntuale").
    """

    __tablename__ = "recensioni"
    __table_args__ = (
        # Una sola recensione per coppia di utenti su uno stesso annuncio.
        UniqueConstraint("autore_id", "destinatario_id", "annuncio_id", name="uq_recensione"),
        CheckConstraint("autore_id <> destinatario_id", name="ck_recensione_no_autorecensione"),
        CheckConstraint("stelle BETWEEN 1 AND 5", name="ck_recensione_stelle"),
        _voto("voto_puntualita"),
        _voto("voto_professionalita"),
        _voto("voto_ambiente"),
        _voto("voto_pagamento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    autore_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destinatario_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Annuncio a cui si riferisce: dà contesto e permette di verificare
    # che i due si siano davvero incontrati su un turno.
    annuncio_id: Mapped[int | None] = mapped_column(
        ForeignKey("annunci.id", ondelete="SET NULL"), index=True
    )

    stelle: Mapped[int] = mapped_column(Integer, nullable=False)
    commento: Mapped[str | None] = mapped_column(Text)

    # Voti di dettaglio, tutti opzionali (1-5).
    voto_puntualita: Mapped[int | None] = mapped_column(Integer)
    voto_professionalita: Mapped[int | None] = mapped_column(Integer)
    voto_ambiente: Mapped[int | None] = mapped_column(Integer)  # bagnino -> piscina
    voto_pagamento: Mapped[int | None] = mapped_column(Integer)  # bagnino -> piscina

    autore: Mapped[Utente] = relationship(
        back_populates="recensioni_scritte", foreign_keys=[autore_id]
    )
    destinatario: Mapped[Utente] = relationship(
        back_populates="recensioni_ricevute", foreign_keys=[destinatario_id]
    )
    annuncio: Mapped[Annuncio | None] = relationship(back_populates="recensioni")

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Recensione {self.autore_id}->{self.destinatario_id} {self.stelle}★>"
