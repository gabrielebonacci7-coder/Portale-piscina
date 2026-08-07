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


settings = Settings()
