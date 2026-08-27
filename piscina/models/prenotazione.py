"""Prenotazioni, postazioni prenotate e occupazione del solarium."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from piscina.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from piscina.models.postazione import Postazione

# Stati di una prenotazione. Non c'è "pagata": si paga in cassa, e il registro
# di cassa è quello della piscina, non questo.
IN_ATTESA = "in_attesa"   # prenotata, il cliente non è ancora arrivato
ARRIVATO = "arrivato"     # ritirata in cassa
ANNULLATA = "annullata"

STATI = (IN_ATTESA, ARRIVATO, ANNULLATA)

# Le due metà della giornata, 9–14 e 14–19. Sono l'unità con cui si misura
# l'occupazione: la giornata intera è semplicemente "tutte e due".
MATTINA = "mattina"
POMERIGGIO = "pomeriggio"
MEZZE = (MATTINA, POMERIGGIO)


class Prenotazione(Base, TimestampMixin):
    """Una prenotazione: un giorno, una fascia, uno o più posti, una persona.

    Non serve un account per prenotare: chi prenota lascia nome, telefono ed
    email, paga in cassa all'arrivo e ritrova la prenotazione con il codice.
    Un registro di iscrizioni, in una piscina comunale dove metà dei clienti
    viene tre volte l'anno, sarebbe solo un ostacolo in più fra la voglia di
    un ombrellone e l'ombrellone.
    """

    __tablename__ = "prenotazioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Cinque caratteri leggibili al telefono: "PC-4KH7Q".
    codice: Mapped[str] = mapped_column(String(10), unique=True, index=True)

    giorno: Mapped[date] = mapped_column(Date, index=True)
    fascia: Mapped[str] = mapped_column(String(12))

    nome: Mapped[str] = mapped_column(String(80))
    telefono: Mapped[str] = mapped_column(String(24), index=True)
    email: Mapped[str] = mapped_column(String(160), index=True)
    persone: Mapped[int] = mapped_column(Integer, default=1)
    note: Mapped[str] = mapped_column(String(300), default="")

    stato: Mapped[str] = mapped_column(String(12), default=IN_ATTESA, index=True)
    # Totale del solo noleggio, in centesimi. Gli ingressi si contano in cassa:
    # dipendono da quante persone sono e da chi è residente.
    totale_cent: Mapped[int] = mapped_column(Integer, default=0)

    righe: Mapped[list["RigaPrenotazione"]] = relationship(
        back_populates="prenotazione", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def codici_postazioni(self) -> list[str]:
        return sorted(r.postazione.codice for r in self.righe)

    def __repr__(self) -> str:
        return f"<Prenotazione {self.codice} {self.giorno} {self.fascia}>"


class RigaPrenotazione(Base):
    """Una postazione dentro una prenotazione, con i lettini che ci vanno sotto."""

    __tablename__ = "righe_prenotazione"
    __table_args__ = (
        UniqueConstraint("prenotazione_id", "postazione_id", name="uq_riga_postazione"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    prenotazione_id: Mapped[int] = mapped_column(
        ForeignKey("prenotazioni.id", ondelete="CASCADE"), index=True
    )
    postazione_id: Mapped[int] = mapped_column(ForeignKey("postazioni.id"), index=True)

    lettini: Mapped[int] = mapped_column(Integer, default=0)
    prezzo_cent: Mapped[int] = mapped_column(Integer, default=0)

    prenotazione: Mapped["Prenotazione"] = relationship(back_populates="righe")
    postazione: Mapped["Postazione"] = relationship(back_populates="righe", lazy="joined")

    occupazioni: Mapped[list["Occupazione"]] = relationship(
        back_populates="riga", cascade="all, delete-orphan"
    )


class Occupazione(Base):
    """Una postazione occupata, in un giorno, per una metà di giornata.

    È la tabella che tiene davvero il posto. Il vincolo di unicità qui sotto
    fa un lavoro che nessun controllo scritto in Python può fare: se due
    persone toccano lo stesso ombrellone nello stesso istante, una delle due
    scritture viene respinta dal database. Con un `if già_occupato` e basta,
    entrambe leggerebbero "libero" e prenoterebbero, e la lite scoppierebbe
    sotto l'ombrellone invece che qui.

    Una giornata intera scrive due righe (mattina e pomeriggio), una mezza
    giornata ne scrive una: la regola "mattina e pomeriggio convivono, la
    giornata intera no" non è scritta da nessuna parte, viene da sé.

    Quando una prenotazione si annulla, le sue occupazioni si cancellano: il
    posto deve tornare libero subito, e la memoria di chi c'era resta nella
    prenotazione.
    """

    __tablename__ = "occupazioni"
    __table_args__ = (
        UniqueConstraint("postazione_id", "giorno", "mezza", name="uq_posto_occupato"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    postazione_id: Mapped[int] = mapped_column(ForeignKey("postazioni.id"), index=True)
    giorno: Mapped[date] = mapped_column(Date, index=True)
    mezza: Mapped[str] = mapped_column(String(12))
    riga_id: Mapped[int] = mapped_column(
        ForeignKey("righe_prenotazione.id", ondelete="CASCADE"), index=True
    )

    riga: Mapped["RigaPrenotazione"] = relationship(back_populates="occupazioni")
