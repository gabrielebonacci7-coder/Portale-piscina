"""Account della bacheca: dati comuni a bagnini e strutture."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import Ruolo, TipoUtente, enum_col

if TYPE_CHECKING:
    from app.models.annuncio import Annuncio
    from app.models.bagnino import ProfiloBagnino
    from app.models.candidatura import Candidatura
    from app.models.messaggistica import Blocco, Partecipante
    from app.models.piscina import ProfiloPiscina
    from app.models.recensione import Recensione
    from app.models.token_email import TokenEmail


class Utente(TimestampMixin, Base):
    """Identità e credenziali.

    I dati anagrafici veri e propri stanno nel profilo collegato: un utente ha
    `ProfiloBagnino` **oppure** `ProfiloPiscina` a seconda di `tipo`.
    """

    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(32), index=True)
    # Hash della password: in chiaro non ci finisce mai nulla.
    password_hash: Mapped[str | None] = mapped_column(String(255))

    tipo: Mapped[TipoUtente] = mapped_column(enum_col(TipoUtente), nullable=False, index=True)
    ruolo: Mapped[Ruolo] = mapped_column(
        enum_col(Ruolo), default=Ruolo.UTENTE, nullable=False, index=True
    )

    attivo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Ha cliccato il link di conferma arrivato per email. Diverso da
    # `verificato`, che riguarda i documenti controllati dallo staff.
    email_verificata: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Contatto verificato / documenti controllati dallo staff.
    verificato: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Se False il numero non è pubblico e si passa dai messaggi interni.
    telefono_pubblico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profilo_bagnino: Mapped[ProfiloBagnino | None] = relationship(
        back_populates="utente", cascade="all, delete-orphan", uselist=False
    )
    profilo_piscina: Mapped[ProfiloPiscina | None] = relationship(
        back_populates="utente", cascade="all, delete-orphan", uselist=False
    )

    # `annunci` punta ad annunci.autore_id; `annunci_assegnati` ad annunci.assegnato_a_id.
    # Con due FK verso la stessa tabella `foreign_keys` non è opzionale.
    annunci: Mapped[list[Annuncio]] = relationship(
        back_populates="autore",
        foreign_keys="Annuncio.autore_id",
        cascade="all, delete-orphan",
    )
    annunci_assegnati: Mapped[list[Annuncio]] = relationship(
        back_populates="assegnato_a", foreign_keys="Annuncio.assegnato_a_id"
    )

    candidature: Mapped[list[Candidatura]] = relationship(
        back_populates="candidato", cascade="all, delete-orphan"
    )

    token_email: Mapped[list[TokenEmail]] = relationship(
        back_populates="utente", cascade="all, delete-orphan"
    )

    partecipazioni: Mapped[list[Partecipante]] = relationship(
        back_populates="utente", cascade="all, delete-orphan"
    )
    blocchi_effettuati: Mapped[list[Blocco]] = relationship(
        back_populates="bloccante",
        foreign_keys="Blocco.bloccante_id",
        cascade="all, delete-orphan",
    )
    blocchi_subiti: Mapped[list[Blocco]] = relationship(
        back_populates="bloccato",
        foreign_keys="Blocco.bloccato_id",
        cascade="all, delete-orphan",
    )

    recensioni_scritte: Mapped[list[Recensione]] = relationship(
        back_populates="autore",
        foreign_keys="Recensione.autore_id",
        cascade="all, delete-orphan",
    )
    recensioni_ricevute: Mapped[list[Recensione]] = relationship(
        back_populates="destinatario",
        foreign_keys="Recensione.destinatario_id",
        cascade="all, delete-orphan",
    )

    @property
    def e_staff(self) -> bool:
        return self.ruolo == Ruolo.STAFF

    @property
    def profilo(self) -> ProfiloBagnino | ProfiloPiscina | None:
        """Il profilo giusto in base al tipo di account."""
        return self.profilo_bagnino if self.tipo == TipoUtente.BAGNINO else self.profilo_piscina

    @property
    def nome_visualizzato(self) -> str:
        """Nome da mostrare in bacheca. Ripiega sull'email se manca il profilo."""
        if self.tipo == TipoUtente.BAGNINO and self.profilo_bagnino:
            return self.profilo_bagnino.nome_completo
        if self.tipo == TipoUtente.PISCINA and self.profilo_piscina:
            return self.profilo_piscina.nome_struttura
        return self.email

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<Utente {self.id} {self.email} ({self.tipo})>"
