"""Configurazione, letta da variabili d'ambiente o dal file .env.

Tutte le variabili hanno il prefisso `REFORMER_`: lo stesso server (e magari
lo stesso file .env) può ospitare anche altri progetti, e senza prefisso si
scriverebbero addosso (SECRET_KEY, EMAIL_SMTP_HOST...).
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Radice del repository (la cartella che contiene "reformer/").
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="REFORMER_", extra="ignore")

    app_name: str = "RE FORMER"
    debug: bool = True

    database_url: str = f"sqlite:///{BASE_DIR / 'reformer.db'}"

    # --- Sicurezza --------------------------------------------------------
    # Firma i token di accesso. Questo valore è SOLO per lo sviluppo: online
    # va impostata REFORMER_SECRET_KEY con un valore casuale, per esempio
    # `python -c "import secrets; print(secrets.token_hex(32))"`.
    secret_key: str = "dev-only-chiave-non-usare-in-produzione-0123456789abcdef"
    algorithm: str = "HS256"
    bcrypt_rounds: int = 12
    # Le clienti aprono l'app dal telefono una o due volte a settimana: farle
    # rientrare ogni giorno sarebbe solo una seccatura.
    giorni_validita_token: int = 60
    ore_validita_verifica: int = 48
    minuti_validita_recupero: int = 60

    # --- Staff ------------------------------------------------------------
    # Chi si registra con uno di questi indirizzi diventa staff, ma solo dopo
    # aver confermato l'email: senza conferma chiunque potrebbe scrivere
    # l'indirizzo di Greta e prendersi il gestionale.
    email_staff: str = "greta.lorenzetti@icloud.com,elisabonacci@yahoo.it"

    # --- Email ------------------------------------------------------------
    # Senza host SMTP niente parte davvero: il messaggio finisce nel log.
    email_smtp_host: str = ""
    email_smtp_porta: int = 587
    email_smtp_utente: str = ""
    email_smtp_password: str = ""
    email_mittente: str = "RE FORMER <no-reply@example.com>"

    url_pubblico: str = "http://127.0.0.1:8002"
    dietro_proxy: bool = False

    # --- Regole dello studio ----------------------------------------------
    posti_per_lezione: int = 3
    ore_disdetta: int = 12
    giorni_prenotabili: int = 30
    # Chi ha finito le lezioni può prenotare lo stesso e saldare in studio,
    # ma fino a un certo punto: senza tetto, chiunque si registri potrebbe
    # occupare tutti i posti del mese senza aver pagato niente.
    max_lezioni_da_saldare: int = 2
    fuso_orario: str = "Europe/Rome"

    # Promemoria: si manda quando alla lezione mancano meno di queste ore.
    ore_promemoria: int = 24
    promemoria_attivi: bool = True

    # --- Limiti ai tentativi ----------------------------------------------
    finestra_limiti_minuti: int = 60
    max_accessi: int = 10
    max_registrazioni_per_ip: int = 8
    max_email_per_ip: int = 6

    @property
    def indirizzi_staff(self) -> set[str]:
        return {x.strip().lower() for x in self.email_staff.split(",") if x.strip()}

    @property
    def chiave_di_sviluppo(self) -> bool:
        return self.secret_key.startswith("dev-only")


settings = Settings()
