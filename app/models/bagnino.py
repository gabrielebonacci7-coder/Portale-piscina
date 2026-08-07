"""Profilo bagnino e le sue entità satellite: brevetti, esperienze, disponibilità."""

from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import TipoBrevetto, enum_col
from app.models.zona import bagnino_zone

if TYPE_CHECKING:
    from app.models.piscina import ProfiloPiscina
    from app.models.utente import Utente
    from app.models.zona import Zona


class ProfiloBagnino(TimestampMixin, Base):
    """Il "mini LinkedIn" del bagnino."""

    __tablename__ = "profili_bagnino"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    cognome: Mapped[str] = mapped_column(String(80), nullable=False)
    # Si salva la data di nascita, non l'età: l'età si calcola e non invecchia male.
    data_nascita: Mapped[date | None] = mapped_column(Date)

    citta: Mapped[str] = mapped_column(String(80), default="Roma", nullable=False, index=True)
    # Testo libero per le note di spostamento ("solo zone raggiungibili in metro B").
    note_spostamenti: Mapped[str | None] = mapped_column(String(255))

    # Riassunto veloce mostrato in bacheca.
    anni_esperienza: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)

    # Accetta anche una singola giornata / turno spot, non solo contratti continuativi.
    disponibile_chiamata_singola: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    # Il profilo è visibile in bacheca e cercabile dalle strutture.
    cerca_lavoro: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    utente: Mapped[Utente] = relationship(back_populates="profilo_bagnino")
    zone: Mapped[list[Zona]] = relationship(secondary=bagnino_zone, back_populates="bagnini")
    brevetti: Mapped[list[Brevetto]] = relationship(
        back_populates="bagnino", cascade="all, delete-orphan"
    )
    esperienze: Mapped[list[Esperienza]] = relationship(
        back_populates="bagnino", cascade="all, delete-orphan", order_by="Esperienza.data_inizio.desc()"
    )
    disponibilita: Mapped[list[Disponibilita]] = relationship(
        back_populates="bagnino", cascade="all, delete-orphan"
    )

    @property
    def nome_completo(self) -> str:
        return f"{self.nome} {self.cognome}".strip()

    @property
    def eta(self) -> int | None:
        """Età in anni compiuti, derivata da `data_nascita`."""
        if self.data_nascita is None:
            return None
        oggi = date.today()
        return (
            oggi.year
            - self.data_nascita.year
            - ((oggi.month, oggi.day) < (self.data_nascita.month, self.data_nascita.day))
        )

    @property
    def brevetti_validi(self) -> list[Brevetto]:
        return [b for b in self.brevetti if b.valido]

    @property
    def abilitato(self) -> bool:
        """True se ha almeno un brevetto non scaduto: requisito per candidarsi."""
        return bool(self.brevetti_validi)

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<ProfiloBagnino {self.id} {self.nome_completo}>"


class Brevetto(TimestampMixin, Base):
    """Brevetto di salvamento. Un bagnino può averne più di uno (P, IP, MIP...)."""

    __tablename__ = "brevetti"

    id: Mapped[int] = mapped_column(primary_key=True)
    bagnino_id: Mapped[int] = mapped_column(
        ForeignKey("profili_bagnino.id", ondelete="CASCADE"), nullable=False, index=True
    )

    tipo: Mapped[TipoBrevetto] = mapped_column(enum_col(TipoBrevetto), nullable=False)
    ente: Mapped[str] = mapped_column(String(80), default="FIN", nullable=False)
    numero: Mapped[str | None] = mapped_column(String(64))

    data_rilascio: Mapped[date | None] = mapped_column(Date)
    # Il rinnovo FIN dura di norma due anni: qui sta il "da verificare se scaduto".
    data_scadenza: Mapped[date | None] = mapped_column(Date, index=True)

    # True quando lo staff ha visto il documento originale.
    verificato: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    bagnino: Mapped[ProfiloBagnino] = relationship(back_populates="brevetti")

    @property
    def valido(self) -> bool:
        """Scaduto o no. Senza data di scadenza si considera non valido: va verificato."""
        if self.data_scadenza is None:
            return False
        return self.data_scadenza >= date.today()

    @property
    def giorni_alla_scadenza(self) -> int | None:
        if self.data_scadenza is None:
            return None
        return (self.data_scadenza - date.today()).days

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Brevetto {self.tipo} scad. {self.data_scadenza}>"


class Esperienza(TimestampMixin, Base):
    """Una riga di curriculum: dove ha lavorato e per quanto."""

    __tablename__ = "esperienze"

    id: Mapped[int] = mapped_column(primary_key=True)
    bagnino_id: Mapped[int] = mapped_column(
        ForeignKey("profili_bagnino.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Se la struttura è iscritta al portale la si collega, altrimenti resta il testo libero.
    piscina_id: Mapped[int | None] = mapped_column(
        ForeignKey("profili_piscina.id", ondelete="SET NULL"), index=True
    )

    struttura: Mapped[str] = mapped_column(String(150), nullable=False)
    zona: Mapped[str | None] = mapped_column(String(80))
    mansione: Mapped[str | None] = mapped_column(String(120))

    data_inizio: Mapped[date | None] = mapped_column(Date)
    data_fine: Mapped[date | None] = mapped_column(Date)  # None = tuttora in corso
    stagioni: Mapped[int | None] = mapped_column(Integer)

    descrizione: Mapped[str | None] = mapped_column(Text)

    bagnino: Mapped[ProfiloBagnino] = relationship(back_populates="esperienze")
    piscina: Mapped[ProfiloPiscina | None] = relationship(back_populates="esperienze_collegate")

    @property
    def in_corso(self) -> bool:
        return self.data_fine is None

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Esperienza {self.struttura}>"


class Disponibilita(Base):
    """Fascia oraria ricorrente settimanale (lun=0 ... dom=6)."""

    __tablename__ = "disponibilita"
    __table_args__ = (
        CheckConstraint("giorno_settimana BETWEEN 0 AND 6", name="ck_disponibilita_giorno"),
        CheckConstraint("ora_fine > ora_inizio", name="ck_disponibilita_fascia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bagnino_id: Mapped[int] = mapped_column(
        ForeignKey("profili_bagnino.id", ondelete="CASCADE"), nullable=False, index=True
    )

    giorno_settimana: Mapped[int] = mapped_column(Integer, nullable=False)
    ora_inizio: Mapped[time] = mapped_column(Time, nullable=False)
    ora_fine: Mapped[time] = mapped_column(Time, nullable=False)

    note: Mapped[str | None] = mapped_column(String(255))

    bagnino: Mapped[ProfiloBagnino] = relationship(back_populates="disponibilita")

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Disponibilita g{self.giorno_settimana} {self.ora_inizio}-{self.ora_fine}>"
