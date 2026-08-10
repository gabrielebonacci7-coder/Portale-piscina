"""Configurazione applicativa, letta da variabili d'ambiente o da un file .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Radice del progetto (cartella che contiene "app/")
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Guardlink API"
    debug: bool = True

    # Percorso del file SQLite; sovrascrivibile con DATABASE_URL per passare
    # in futuro a PostgreSQL senza toccare il codice.
    database_url: str = f"sqlite:///{BASE_DIR / 'guardlink.db'}"

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

    # --- Email ------------------------------------------------------------
    # Senza host SMTP le email non partono: finiscono nel log con il link in
    # chiaro. Comodo in sviluppo, da configurare prima di andare online.
    email_smtp_host: str = ""
    email_smtp_porta: int = 587
    email_smtp_utente: str = ""
    email_smtp_password: str = ""
    email_mittente: str = "Guardlink <no-reply@guardlink.example>"

    # Indirizzo pubblico dell'app: serve a costruire i link delle email.
    url_pubblico: str = "http://127.0.0.1:8000"

    # Il recupero password vale poco: è la chiave di un account, e chi la
    # chiede la usa subito. La verifica dell'indirizzo può aspettare.
    minuti_validita_recupero: int = 30
    ore_validita_verifica: int = 48

    # --- Rete e proxy -----------------------------------------------------
    # In produzione l'app sta dietro a Caddy, che le passa l'IP vero del
    # visitatore in `X-Forwarded-For`. Ci si fida di quell'intestazione **solo**
    # se questa è True: altrimenti chiunque potrebbe scriverci dentro un IP
    # falso e aggirare i limiti sui tentativi di accesso.
    dietro_proxy: bool = False

    # --- Limiti sui tentativi ---------------------------------------------
    # Senza, si possono provare password all'infinito.
    #
    # I limiti **per indirizzo email** sono stretti: sono quelli che proteggono
    # davvero un account, e riguardano una persona sola.
    # I limiti **per IP** sono larghi apposta: in una piscina i bagnini stanno
    # tutti sullo stesso wi-fi e per il server hanno lo stesso indirizzo. Un
    # numero basso lì non fermerebbe nessun attacco — chi ci prova davvero usa
    # tanti IP — ma chiuderebbe fuori mezzo spogliatoio.
    limite_login: int = 30           # per IP, ogni finestra
    limite_login_per_email: int = 5  # per indirizzo, ogni finestra
    limite_registrazioni: int = 15   # per IP, ogni finestra
    limite_recuperi: int = 5         # per IP, ogni finestra
    finestra_limiti_minuti: int = 15

    # --- Foto -------------------------------------------------------------
    # Dove finiscono le foto caricate. In produzione conviene un disco
    # separato o uno spazio oggetti, non la cartella del codice.
    media_dir: str = str(BASE_DIR / "media")
    # 12 MB: una foto da telefono ci sta larga, e il server non si intasa.
    max_upload_bytes: int = 12 * 1024 * 1024
    foto_lato_max: int = 1600
    foto_lato_anteprima: int = 400
    # Quante foto può avere una struttura.
    max_foto_piscina: int = 6
    # Durata del token di accesso: 7 giorni, comodo per una PWA su telefono.
    access_token_expire_minutes: int = 60 * 24 * 7


settings = Settings()
