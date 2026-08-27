"""Password e token di accesso dello staff."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from piscina.core.config import settings

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
        # Hash malformato in database: nega l'accesso invece di esplodere.
        return False


def crea_token(operatore_id: int) -> str:
    adesso = datetime.now(timezone.utc)
    payload = {
        "sub": str(operatore_id),
        "iat": adesso,
        "exp": adesso + timedelta(hours=settings.ore_validita_token),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def leggi_token(token: str) -> int | None:
    """Id dell'operatore, o None se il token è scaduto o falso."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (jwt.InvalidTokenError, TypeError, ValueError):
        return None
