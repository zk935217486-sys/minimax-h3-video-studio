from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """Raised when a required production setting is missing or invalid."""


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True)
class Settings:
    database_path: Path
    jwt_secret: str
    jwt_expire_minutes: int
    cors_origins: tuple[str, ...]
    official_api_key: str | None
    comfyui_url: str
    demo_mode: bool

    @classmethod
    def from_env(cls) -> "Settings":
        environment = os.getenv("APP_ENV", "development").lower()
        secret = os.getenv("JWT_SECRET", "")
        if environment == "production" and len(secret) < 32:
            raise ConfigError("JWT_SECRET must contain at least 32 characters in production")
        if not secret:
            secret = "development-only-change-this-secret"

        database_path = Path(os.getenv("DATABASE_PATH", "data/minimax_h3.sqlite3"))
        origins = tuple(origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8787").split(",") if origin.strip())
        return cls(
            database_path=database_path,
            jwt_secret=secret,
            jwt_expire_minutes=_positive_int("JWT_EXPIRE_MINUTES", 30),
            cors_origins=origins,
            official_api_key=os.getenv("MINIMAX_API_KEY") or None,
            comfyui_url=os.getenv("COMFYUI_URL", "http://localhost:8188"),
            demo_mode=os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes"},
        )


settings = Settings.from_env()
