"""Configurazione applicativa, letta da variabili d'ambiente o da un file .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Radice del progetto (cartella che contiene "app/")
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Portale Piscina API"
    debug: bool = True

    # Percorso del file SQLite; sovrascrivibile con DATABASE_URL per passare
    # in futuro a PostgreSQL senza toccare il codice.
    database_url: str = f"sqlite:///{BASE_DIR / 'portale_piscina.db'}"

    # Città di default della bacheca (per ora Roma).
    citta_default: str = "Roma"

    # --- Sicurezza --------------------------------------------------------
    # Chiave di firma dei token. Questo valore è SOLO per lo sviluppo locale:
    # in produzione va impostata la variabile d'ambiente SECRET_KEY con un
    # valore casuale (es. `python -c "import secrets; print(secrets.token_hex(32))"`).
    # Cambiandola, tutti i token già emessi smettono di valere.
    secret_key: str = "dev-only-chiave-non-usare-in-produzione-0123456789abcdef"
    algorithm: str = "HS256"
    # Costo del calcolo bcrypt. 12 è il valore giusto in esercizio; i test lo
    # abbassano via BCRYPT_ROUNDS perché altrimenti impiegherebbero minuti.
    bcrypt_rounds: int = 12
    # Durata del token di accesso: 7 giorni, comodo per una PWA su telefono.
    access_token_expire_minutes: int = 60 * 24 * 7


settings = Settings()
