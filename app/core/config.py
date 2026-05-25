"""
settings desde .env sin secretos en repo
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # base de datos
    DATABASE_URL: str = (
        "postgresql://postgres:1234postgres@localhost:5434/parcial_prog4"
    )

    # jwt (cookie en login)
    SECRET_KEY: str  # obligatorio en .env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # bcrypt rounds (>=12)
    BCRYPT_ROUNDS: int = 12

    # cors: lista separada por coma
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_min_length(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("SECRET_KEY debe tener al menos 16 caracteres")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()

