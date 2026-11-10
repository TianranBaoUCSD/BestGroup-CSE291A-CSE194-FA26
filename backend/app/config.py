"""Settings read from environment variables or the project's .env (see ../.env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Real environment variables win over .env, so Docker and managed hosts are unaffected.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


@dataclass(frozen=True)
class Settings:
    # e.g. postgresql+psycopg://bayarea:secret@localhost:5432/bayarea
    database_url: str = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://bayarea:bayarea@localhost:5432/bayarea"
    )
    db_pool_size: int = _int("DB_POOL_SIZE", 5)
    db_max_overflow: int = _int("DB_MAX_OVERFLOW", 10)
    db_pool_recycle_s: int = _int("DB_POOL_RECYCLE_S", 1800)
    db_echo: bool = os.environ.get("DB_ECHO", "false").lower() == "true"


settings = Settings()
