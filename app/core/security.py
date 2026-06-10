# bcrypt y jwt mirar settings
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings


@lru_cache
def _pwd_context() -> CryptContext:
    s = get_settings()
    return CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=s.BCRYPT_ROUNDS,
    )


def hash_password(plain: str) -> str:
    return _pwd_context().hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context().verify(plain, hashed)


def create_access_token(*, subject_email: str, user_id: int, roles: list[str]) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=s.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject_email,
        "uid": user_id,
        "roles": roles,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, s.SECRET_KEY, algorithm=s.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    s = get_settings()
    try:
        return jwt.decode(token, s.SECRET_KEY, algorithms=[s.JWT_ALGORITHM])
    except JWTError:
        raise


def generar_refresh_token() -> str:
    # token plano de alta entropia (va en la cookie)
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    # sha256 alcanza: el token ya es aleatorio y largo
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_expira_en() -> datetime:
    s = get_settings()
    return datetime.now(timezone.utc) + timedelta(days=s.REFRESH_TOKEN_EXPIRE_DAYS)
