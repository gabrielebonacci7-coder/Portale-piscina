"""Controlli che si fanno all'accensione, prima di accettare la prima richiesta.

Il punto di tutto questo file: **in produzione l'app deve rifiutarsi di partire
male**, invece di partire e sembrare a posto. Un server che va online con la
chiave di firma di sviluppo funziona benissimo — e chiunque conosca quella
chiave, cioè chiunque abbia letto il codice su GitHub, può fabbricarsi un token
valido per qualsiasi account. Un guasto all'avvio si nota in trenta secondi;
questo non si noterebbe mai.
"""

from app.core.config import settings

CHIAVE_DI_SVILUPPO = "dev-only-chiave-non-usare-in-produzione-0123456789abcdef"

INDIRIZZI_LOCALI = ("127.0.0.1", "localhost", "0.0.0.0", "[::1]")


class ConfigurazioneNonValida(RuntimeError):
    """Manca qualcosa che in produzione non può mancare."""


def in_produzione() -> bool:
    """Due indizi indipendenti, perché uno solo si dimentica.

    `debug=False` è la dichiarazione esplicita; un `URL_PUBBLICO` che non punta
    a questo computer è il fatto. Basta uno dei due: chi mette l'indirizzo vero
    e si scorda `DEBUG=false` è comunque online, e va protetto lo stesso.
    """
    url = settings.url_pubblico.lower()
    pubblico = not any(locale in url for locale in INDIRIZZI_LOCALI)
    return (not settings.debug) or pubblico


def verifica_configurazione() -> list[str]:
    """Elenco dei problemi. Vuoto = si può partire."""
    if not in_produzione():
        return []

    problemi = []

    if settings.secret_key == CHIAVE_DI_SVILUPPO:
        problemi.append(
            "SECRET_KEY è ancora quella di sviluppo, che sta scritta nel codice: "
            "chiunque potrebbe firmarsi un token valido per qualsiasi account.\n"
            '    Generane una con:  python -c "import secrets; print(secrets.token_hex(32))"'
        )

    if settings.debug:
        problemi.append(
            "DEBUG è attivo su un indirizzo pubblico: CORS accetta qualsiasi "
            "origine e gli errori mostrano il codice interno.\n"
            "    Imposta DEBUG=false."
        )

    if not settings.url_pubblico.startswith("https://"):
        problemi.append(
            "URL_PUBBLICO non è in https. Senza certificato il service worker "
            "non parte: niente installazione sul telefono e niente "
            "aggiornamenti."
        )

    if not settings.email_smtp_host:
        problemi.append(
            "EMAIL_SMTP_HOST non è impostato: chi dimentica la password resta "
            "fuori per sempre, perché il link non parte.\n"
            "    Vedi il README, «Far partire le email davvero»."
        )

    return problemi


def controlla_o_esplodi() -> None:
    """Chiamata dal `lifespan`: o la configurazione regge, o non si parte."""
    problemi = verifica_configurazione()
    if not problemi:
        return
    elenco = "\n\n".join(f"  {n}. {p}" for n, p in enumerate(problemi, 1))
    raise ConfigurazioneNonValida(
        "\n\nGuardlink non parte: la configurazione non è adatta a stare "
        f"online.\n\n{elenco}\n\n"
        "  (In locale questi controlli non scattano: si attivano quando "
        "URL_PUBBLICO\n   non punta più a questo computer, oppure con "
        "DEBUG=false.)\n"
    )
