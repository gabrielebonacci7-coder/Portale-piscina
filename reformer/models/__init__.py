"""Le tabelle.

Una sola cartella e un solo file: sono otto tabelle piccole, e averle tutte
sott'occhio insieme aiuta più che saltare fra otto file.

- **Utente**: clienti e staff (Greta ed Elisa). Il saldo delle lezioni sta
  qui, e ogni sua variazione lascia una riga in **Movimento**.
- **Lezione**: una per ogni ora del calendario. Le righe si creano da sole,
  seguendo l'orario della settimana (`dominio/orario.py`), quando qualcuno
  guarda quei giorni.
- **Prenotazione**: chi è iscritta a quale lezione. Una disdetta non cancella
  la riga: la marca come disdetta, così resta lo storico.
- **Attesa**: la lista d'attesa di una lezione piena, in ordine d'arrivo.
- **Notifica**: i messaggi personali nella campanella dell'app.
- **Avviso**: i messaggi dello studio a tutte.
- **TokenEmail**: i link monouso per confermare l'email e cambiare password.
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from reformer.db.base import Base, TimestampMixin, UTCDateTime, utcnow


class Ruolo(str, enum.Enum):
    CLIENTE = "cliente"
    STAFF = "staff"


class StatoPrenotazione(str, enum.Enum):
    ATTIVA = "attiva"
    DISDETTA = "disdetta"        # l'ha tolta la cliente, in tempo
    TOLTA = "tolta"              # l'ha tolta lo studio
    ANNULLATA = "annullata"      # la lezione intera è stata annullata


class TipoToken(str, enum.Enum):
    VERIFICA_EMAIL = "verifica_email"
    RECUPERO_PASSWORD = "recupero_password"


class Utente(TimestampMixin, Base):
    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    nome: Mapped[str] = mapped_column(String(80))
    cognome: Mapped[str] = mapped_column(String(80))
    telefono: Mapped[str] = mapped_column(String(30), default="")
    ruolo: Mapped[Ruolo] = mapped_column(Enum(Ruolo, native_enum=False), default=Ruolo.CLIENTE)

    email_verificata_il: Mapped[datetime | None] = mapped_column(UTCDateTime)
    privacy_accettata_il: Mapped[datetime | None] = mapped_column(UTCDateTime)
    versione_privacy: Mapped[str | None] = mapped_column(String(20))

    # Lezioni ancora da fare, pagate in studio. Può andare sotto zero: chi ha
    # finito il pacchetto può prenotare lo stesso e salda alla lezione.
    lezioni_rimaste: Mapped[int] = mapped_column(Integer, default=0)
    # Facoltativa, solo informativa: lo studio decide cosa fare se scade.
    scadenza: Mapped[date | None] = mapped_column(Date)

    # Alzato a ogni cambio password: invalida i token già emessi.
    sessione: Mapped[int] = mapped_column(Integer, default=0)
    # Fino a quando ha visto gli avvisi dello studio (per il pallino "nuovo").
    avvisi_visti_il: Mapped[datetime | None] = mapped_column(UTCDateTime)
    # Account cancellato su richiesta: i dati personali sono già stati tolti.
    cancellato_il: Mapped[datetime | None] = mapped_column(UTCDateTime)

    prenotazioni: Mapped[list["Prenotazione"]] = relationship(back_populates="utente")

    @property
    def e_staff(self) -> bool:
        return self.ruolo == Ruolo.STAFF

    @property
    def nome_completo(self) -> str:
        return f"{self.nome} {self.cognome}".strip()


class Lezione(TimestampMixin, Base):
    __tablename__ = "lezioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Inizio in UTC. Unico: è quello che identifica la lezione.
    inizio: Mapped[datetime] = mapped_column(UTCDateTime, unique=True, index=True)
    durata_minuti: Mapped[int] = mapped_column(Integer, default=60)
    istruttrice: Mapped[str] = mapped_column(String(20))  # "greta" | "elisa"
    titolo: Mapped[str] = mapped_column(String(60), default="Pilates")
    posti: Mapped[int] = mapped_column(Integer, default=3)
    annullata_il: Mapped[datetime | None] = mapped_column(UTCDateTime)
    motivo_annullamento: Mapped[str | None] = mapped_column(String(200))

    prenotazioni: Mapped[list["Prenotazione"]] = relationship(back_populates="lezione")
    attese: Mapped[list["Attesa"]] = relationship(
        back_populates="lezione", order_by="Attesa.creato_il, Attesa.id"
    )

    @property
    def attive(self) -> list["Prenotazione"]:
        return [p for p in self.prenotazioni if p.stato == StatoPrenotazione.ATTIVA]

    @property
    def liberi(self) -> int:
        return max(self.posti - len(self.attive), 0)


class Prenotazione(TimestampMixin, Base):
    __tablename__ = "prenotazioni"
    __table_args__ = (
        # Una cliente non può avere due prenotazioni attive sulla stessa
        # lezione. È il database a garantirlo, non solo il codice.
        Index(
            "uq_prenotazione_attiva",
            "lezione_id",
            "utente_id",
            unique=True,
            sqlite_where=text("stato = 'ATTIVA'"),
            postgresql_where=text("stato = 'ATTIVA'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lezione_id: Mapped[int] = mapped_column(ForeignKey("lezioni.id"), index=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), index=True)
    stato: Mapped[StatoPrenotazione] = mapped_column(
        Enum(StatoPrenotazione, native_enum=False), default=StatoPrenotazione.ATTIVA
    )
    # None = non ancora segnata; True/False = presente/assente.
    presente: Mapped[bool | None] = mapped_column(Boolean)
    dalla_lista: Mapped[bool] = mapped_column(Boolean, default=False)
    aggiunta_da_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    chiusa_il: Mapped[datetime | None] = mapped_column(UTCDateTime)
    promemoria_il: Mapped[datetime | None] = mapped_column(UTCDateTime)

    lezione: Mapped[Lezione] = relationship(back_populates="prenotazioni")
    utente: Mapped[Utente] = relationship(back_populates="prenotazioni")


class Attesa(Base):
    __tablename__ = "attese"
    __table_args__ = (UniqueConstraint("lezione_id", "utente_id", name="uq_attesa"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lezione_id: Mapped[int] = mapped_column(ForeignKey("lezioni.id"), index=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), index=True)
    creato_il: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    lezione: Mapped[Lezione] = relationship(back_populates="attese")
    utente: Mapped[Utente] = relationship()


class Movimento(Base):
    """Ogni variazione del saldo lezioni: chi, quanto, perché.

    Serve a rispondere alla domanda che prima o poi arriva: "ma io non avevo
    ancora tre lezioni?". Con questo elenco la risposta si legge in un attimo.
    """

    __tablename__ = "movimenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), index=True)
    autore_id: Mapped[int | None] = mapped_column(ForeignKey("utenti.id"))
    variazione: Mapped[int] = mapped_column(Integer)
    saldo: Mapped[int] = mapped_column(Integer)  # dopo la variazione
    motivo: Mapped[str] = mapped_column(String(200))
    lezione_id: Mapped[int | None] = mapped_column(ForeignKey("lezioni.id"))
    creato_il: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

    autore: Mapped[Utente | None] = relationship(foreign_keys=[autore_id])


class Notifica(Base):
    __tablename__ = "notifiche"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), index=True)
    testo: Mapped[str] = mapped_column(Text)
    creato_il: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    letta_il: Mapped[datetime | None] = mapped_column(UTCDateTime)


class Avviso(Base):
    __tablename__ = "avvisi"

    id: Mapped[int] = mapped_column(primary_key=True)
    autore_id: Mapped[int | None] = mapped_column(ForeignKey("utenti.id"))
    testo: Mapped[str] = mapped_column(Text)
    creato_il: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

    autore: Mapped[Utente | None] = relationship()


class TitoloFisso(Base):
    """Il nome di una lezione che si ripete ogni settimana (es. ogni lunedì
    alle 16:30 "Pilates fitness"). Lo scelgono Greta ed Elisa dal gestionale;
    le lezioni future di quel giorno e ora lo prendono da sole."""

    __tablename__ = "titoli_fissi"
    __table_args__ = (UniqueConstraint("giorno", "ora", name="uq_titolo_fisso"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    giorno: Mapped[int] = mapped_column(Integer)   # lunedì = 0
    ora: Mapped[str] = mapped_column(String(5))    # "16:30", ora di Roma
    titolo: Mapped[str] = mapped_column(String(60))


class TokenEmail(Base):
    """Link monouso. Nel database c'è solo l'impronta del codice: chi leggesse
    la tabella non potrebbe usarli."""

    __tablename__ = "token_email"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), index=True)
    tipo: Mapped[TipoToken] = mapped_column(Enum(TipoToken, native_enum=False))
    impronta: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scade_il: Mapped[datetime] = mapped_column(UTCDateTime)
    usato_il: Mapped[datetime | None] = mapped_column(UTCDateTime)
    creato_il: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    utente: Mapped[Utente] = relationship()

    @property
    def valido(self) -> bool:
        return self.usato_il is None and self.scade_il > utcnow()


__all__ = [
    "Attesa", "Avviso", "Lezione", "Movimento", "Notifica", "Prenotazione",
    "Ruolo", "StatoPrenotazione", "TipoToken", "TitoloFisso", "TokenEmail", "Utente",
]
