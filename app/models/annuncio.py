"""L'annuncio: il cuore della bacheca."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.db.types import UTCDateTime
from app.models.enums import (
    StatoAnnuncio,
    TipoAnnuncio,
    TipoBrevetto,
    TipoCompenso,
    TipoTurno,
    enum_col,
)

if TYPE_CHECKING:
    from app.models.candidatura import Candidatura
    from app.models.piscina import ProfiloPiscina
    from app.models.recensione import Recensione
    from app.models.utente import Utente
    from app.models.zona import Zona


class Annuncio(TimestampMixin, Base):
    """Un turno da coprire, pubblicato da una struttura o da un bagnino."""

    __tablename__ = "annunci"
    __table_args__ = (
        CheckConstraint("data_fine IS NULL OR data_fine >= data_inizio", name="ck_annuncio_date"),
        CheckConstraint("compenso IS NULL OR compenso >= 0", name="ck_annuncio_compenso"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- Chi pubblica -----------------------------------------------------
    autore_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoAnnuncio] = mapped_column(enum_col(TipoAnnuncio), nullable=False, index=True)
    # Struttura di riferimento: compilata quando l'autore è una piscina, ma anche
    # quando un bagnino cerca sostituzione per una struttura iscritta al portale.
    piscina_id: Mapped[int | None] = mapped_column(
        ForeignKey("profili_piscina.id", ondelete="SET NULL"), index=True
    )

    titolo: Mapped[str] = mapped_column(String(150), nullable=False)

    # --- Data e orario ----------------------------------------------------
    data_inizio: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, index=True)
    data_fine: Mapped[datetime | None] = mapped_column(UTCDateTime)

    # --- Dove -------------------------------------------------------------
    citta: Mapped[str] = mapped_column(String(80), default="Roma", nullable=False, index=True)
    zona_id: Mapped[int | None] = mapped_column(
        ForeignKey("zone.id", ondelete="SET NULL"), index=True
    )
    indirizzo: Mapped[str | None] = mapped_column(String(200))

    # --- Compenso ---------------------------------------------------------
    # Numeric(8, 2): niente float sui soldi, si evitano gli arrotondamenti.
    compenso: Mapped[float | None] = mapped_column(Numeric(8, 2))
    compenso_tipo: Mapped[TipoCompenso] = mapped_column(
        enum_col(TipoCompenso), default=TipoCompenso.ORARIO, nullable=False
    )
    valuta: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    # --- Tipo di ingaggio e requisiti ------------------------------------
    tipo_turno: Mapped[TipoTurno] = mapped_column(
        enum_col(TipoTurno), default=TipoTurno.TURNO_FISSO, nullable=False, index=True
    )
    brevetto_richiesto: Mapped[TipoBrevetto | None] = mapped_column(enum_col(TipoBrevetto))
    urgente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    note: Mapped[str | None] = mapped_column(Text)

    # --- Ciclo di vita ----------------------------------------------------
    stato: Mapped[StatoAnnuncio] = mapped_column(
        enum_col(StatoAnnuncio), default=StatoAnnuncio.APERTO, nullable=False, index=True
    )
    # Chi ha preso il turno: chiude il cerchio e abilita le recensioni incrociate.
    assegnato_a_id: Mapped[int | None] = mapped_column(
        ForeignKey("utenti.id", ondelete="SET NULL"), index=True
    )

    autore: Mapped[Utente] = relationship(back_populates="annunci", foreign_keys=[autore_id])
    assegnato_a: Mapped[Utente | None] = relationship(
        back_populates="annunci_assegnati", foreign_keys=[assegnato_a_id]
    )
    piscina: Mapped[ProfiloPiscina | None] = relationship(back_populates="annunci")
    zona: Mapped[Zona | None] = relationship()
    recensioni: Mapped[list[Recensione]] = relationship(back_populates="annuncio")
    candidature: Mapped[list[Candidatura]] = relationship(
        back_populates="annuncio", cascade="all, delete-orphan"
    )

    @property
    def scaduto(self) -> bool:
        return self.data_inizio < datetime.now(timezone.utc)

    @property
    def aperto(self) -> bool:
        return self.stato == StatoAnnuncio.APERTO and not self.scaduto

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Annuncio {self.id} {self.tipo} {self.data_inizio:%d/%m %H:%M}>"
