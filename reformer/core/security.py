"""Password e token di accesso."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from reformer.core.config import settings

# bcrypt tronca in silenzio oltre i 72 byte: meglio rifiutare esplicitamente.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    pwd = password.encode("utf-8")
    if len(pwd) > MAX_PASSWORD_BYTES:
        raise ValueError(f"la password supera i {MAX_PASSWORD_BYTES} byte")
    return bcrypt.hashpw(pwd, bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode()


def verifica_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    pwd = password.encode("utf-8")
    if len(pwd) > MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(pwd, password_hash.encode("utf-8"))
    except ValueError:
        return False


def crea_token(utente_id: int, sessione: int) -> str:
    """`sessione` è un contatore sull'utente: cambiando password lo si alza,
    e tutti i token emessi prima smettono di valere (anche su altri telefoni)."""
    adesso = datetime.now(timezone.utc)
    payload = {
        "sub": str(utente_id),
        "ses": sessione,
        "iat": adesso,
        "exp": adesso + timedelta(days=settings.giorni_validita_token),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def leggi_token(token: str) -> tuple[int, int] | None:
    """(id utente, sessione), o None se il token è scaduto o falso."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return int(payload["sub"]), int(payload.get("ses", 0))
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        return None
