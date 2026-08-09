"""Enumerazioni di dominio condivise fra modelli ORM e schemi Pydantic."""

from enum import Enum

from sqlalchemy import Enum as SAEnum


def enum_col(enum_cls: type[Enum], **kwargs) -> SAEnum:
    """Colonna enum salvata come VARCHAR con il *valore* (non il nome) del membro.

    `native_enum=False` mantiene la portabilità: SQLite non ha un tipo ENUM,
    e su PostgreSQL evitiamo migrazioni dolorose quando si aggiunge un valore.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
        **kwargs,
    )


class TipoUtente(str, Enum):
    """Discriminante fra i due tipi di account della bacheca."""

    BAGNINO = "bagnino"
    PISCINA = "piscina"


class TipoBrevetto(str, Enum):
    """Abilitazioni FIN, dalla più limitata alla più estesa."""

    P = "P"  # Piscina
    IP = "IP"  # Acque interne + piscina
    MIP = "MIP"  # Mare + acque interne + piscina
    ALTRO = "altro"  # Altri enti (SNS, Misericordie, ...) o casi particolari


# I brevetti FIN sono inclusivi: chi ha MIP può fare anche quello che fa un P.
# `ALTRO` non è confrontabile in automatico e non copre nulla: va verificato
# a mano dallo staff (campo `Brevetto.verificato`).
LIVELLO_BREVETTO: dict[str, int] = {"P": 1, "IP": 2, "MIP": 3, "altro": 0}


def brevetto_copre(posseduto: "TipoBrevetto", richiesto: "TipoBrevetto") -> bool:
    """True se `posseduto` è sufficiente per un turno che richiede `richiesto`."""
    livello_posseduto = LIVELLO_BREVETTO[posseduto.value]
    livello_richiesto = LIVELLO_BREVETTO[richiesto.value]
    if livello_posseduto == 0 or livello_richiesto == 0:
        return posseduto == richiesto
    return livello_posseduto >= livello_richiesto


class TipoToken(str, Enum):
    """A cosa serve un codice mandato per email."""

    VERIFICA_EMAIL = "verifica_email"
    RECUPERO_PASSWORD = "recupero_password"


class TipoFoto(str, Enum):
    """A cosa si riferisce la foto di una struttura.

    `INGRESSO` è quella che conta davvero: è come il bagnino riconosce il
    posto quando ci arriva la prima volta, magari di sera e di corsa.
    """

    INGRESSO = "ingresso"
    VASCA = "vasca"
    SPOGLIATOI = "spogliatoi"
    ALTRO = "altro"


class StatoCandidatura(str, Enum):
    INVIATA = "inviata"
    ACCETTATA = "accettata"
    RIFIUTATA = "rifiutata"
    RITIRATA = "ritirata"


class TipoStruttura(str, Enum):
    COMUNALE = "comunale"
    HOTEL = "hotel"
    CONDOMINIO = "condominio"
    CENTRO_SPORTIVO = "centro_sportivo"
    PALESTRA = "palestra"
    PARCO_ACQUATICO = "parco_acquatico"
    CAMPING = "camping"
    PRIVATA = "privata"
    ALTRO = "altro"


class TipoAnnuncio(str, Enum):
    """Chi pubblica e cosa cerca."""

    PISCINA_CERCA_BAGNINO = "piscina_cerca_bagnino"
    BAGNINO_CERCA_SOSTITUZIONE = "bagnino_cerca_sostituzione"


class TipoTurno(str, Enum):
    TURNO_FISSO = "turno_fisso"
    SOSTITUZIONE_URGENTE = "sostituzione_urgente"
    EVENTO_SERALE = "evento_serale"
    STAGIONALE = "stagionale"
    WEEKEND = "weekend"
    ALTRO = "altro"


class TipoCompenso(str, Enum):
    """Unità di misura del compenso proposto nell'annuncio."""

    ORARIO = "orario"
    GIORNALIERO = "giornaliero"
    A_TURNO = "a_turno"
    MENSILE = "mensile"
    DA_CONCORDARE = "da_concordare"


class StatoAnnuncio(str, Enum):
    BOZZA = "bozza"
    APERTO = "aperto"
    ASSEGNATO = "assegnato"
    CHIUSO = "chiuso"
    SCADUTO = "scaduto"
