"""Hashing delle password e token JWT."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

# bcrypt tronca silenziosamente oltre i 72 byte: meglio rifiutare esplicitamente.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Restituisce l'hash bcrypt della password (il salt è incluso nell'hash)."""
    pwd = password.encode("utf-8")
    if len(pwd) > MAX_PASSWORD_BYTES:
        raise ValueError(f"la password supera i {MAX_PASSWORD_BYTES} byte")
    return bcrypt.hashpw(pwd, bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    """Confronta password e hash in tempo costante."""
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


def create_access_token(utente_id: int, expires_delta: timedelta | None = None) -> str:
    """Token di accesso firmato: `sub` contiene l'id dell'utente."""
    scadenza = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": str(utente_id),  # per lo standard JWT `sub` deve essere una stringa
        "exp": scadenza,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> int | None:
    """Verifica firma e scadenza. Restituisce l'id utente, o None se il token non è valido."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (jwt.InvalidTokenError, TypeError, ValueError):
        return None
