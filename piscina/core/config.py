"""Configurazione, letta da variabili d'ambiente o dal file .env.

Tutte le variabili hanno il prefisso `PISCINA_` perché lo stesso file .env
serve anche a Guardlink: senza prefisso i due progetti si scriverebbero
addosso (SECRET_KEY, EMAIL_SMTP_HOST...).
"""

from datetime import date, time
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Radice del repository (la cartella che contiene "piscina/").
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="PISCINA_", extra="ignore"
    )

    app_name: str = "Piscina Comunale Ciampino"
    debug: bool = True

    database_url: str = f"sqlite:///{BASE_DIR / 'piscina.db'}"

    # --- Sicurezza --------------------------------------------------------
    # Firma i token dello staff. Questo valore è SOLO per lo sviluppo: online
    # va impostata PISCINA_SECRET_KEY con un valore casuale, per esempio
    # `python -c "import secrets; print(secrets.token_hex(32))"`.
    secret_key: str = "dev-only-chiave-non-usare-in-produzione-0123456789abcdef"
    algorithm: str = "HS256"
    bcrypt_rounds: int = 12
    ore_validita_token: int = 12

    # --- Email ------------------------------------------------------------
    # Senza host SMTP niente parte davvero: il messaggio finisce nel log.
    # Comodo in sviluppo, da configurare prima di andare online.
    email_smtp_host: str = ""
    email_smtp_porta: int = 587
    email_smtp_utente: str = ""
    email_smtp_password: str = ""
    email_mittente: str = "Piscina Ciampino <no-reply@example.com>"

    # Dove arrivano le prenotazioni: è questa la casella che "collega il
    # gestionale". Più indirizzi si separano con la virgola.
    email_staff: str = ""

    url_pubblico: str = "http://127.0.0.1:8001"
    dietro_proxy: bool = False

    # --- Orari e stagione -------------------------------------------------
    # Dal listino 2026: apertura 9-19, giornata ridotta 9-14 oppure 14-19.
    ora_apertura: time = time(9, 0)
    ora_cambio_fascia: time = time(14, 0)
    ora_chiusura: time = time(19, 0)

    # Quanti giorni avanti si può prenotare.
    giorni_prenotabili: int = 30

    # Stagione estiva: fuori da queste date non si prenota. Vuote = nessun
    # limite (utile in sviluppo, e finché le date non sono decise).
    stagione_inizio: date | None = None
    stagione_fine: date | None = None

    # Quante postazioni può tenere una prenotazione sola: una famiglia può
    # volere due ombrelloni, ma senza un tetto uno prende mezzo solarium.
    max_postazioni_per_prenotazione: int = 4

    # Il listino ha una sola tariffa "al giorno". Finché non ce n'è una per la
    # mezza giornata, mattina e pomeriggio costano come la giornata intera:
    # 0.0 = nessuno sconto, 0.3 = 30% di sconto.
    sconto_mezza_giornata: float = 0.0

    # --- Limiti ai tentativi ----------------------------------------------
    finestra_limiti_minuti: int = 60
    max_prenotazioni_per_ip: int = 12
    max_accessi_staff: int = 10

    @property
    def destinatari_staff(self) -> list[str]:
        return [x.strip() for x in self.email_staff.split(",") if x.strip()]


settings = Settings()
