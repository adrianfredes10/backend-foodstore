# bcrypt y jwt mirar settings
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    s = get_settings()
    return pwd_context.hash(plain, rounds=s.BCRYPT_ROUNDS)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


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
