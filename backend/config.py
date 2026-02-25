"""
config.py — Centralised, type-safe configuration.

Reads values from environment variables / .env file.
Uses plain os.getenv for maximum compatibility with any Pydantic version.

Usage:
    from backend.config import settings

    db_host = settings.db_host
    secret   = settings.secret_key
"""
import os
from dotenv import load_dotenv

load_dotenv()


class _Settings:
    """Centralised config object that wraps os.getenv calls."""

    # ── Security ──────────────────────────────────────────────────────────────
    @property
    def secret_key(self) -> str:
        return os.getenv("SESSION_SECRET_KEY", "change-this-to-a-random-secret-key-in-production")

    @property
    def session_max_age(self) -> int:
        return int(os.getenv("SESSION_MAX_AGE", "86400"))

    # ── Database (Supabase / Postgres) ────────────────────────────────────────
    @property
    def db_host(self) -> str:
        return os.getenv("DB_HOST", "localhost")

    @property
    def db_name(self) -> str:
        return os.getenv("DB_NAME", "postgres")

    @property
    def db_user(self) -> str:
        return os.getenv("DB_USER", "postgres")

    @property
    def db_pass(self) -> str:
        return os.getenv("DB_PASS", "")

    @property
    def db_port(self) -> int:
        return int(os.getenv("DB_PORT", "5432"))

    # ── Application ───────────────────────────────────────────────────────────
    @property
    def app_name(self) -> str:
        return os.getenv("APP_NAME", "Smart Lab Report Analyser")

    @property
    def app_version(self) -> str:
        return os.getenv("APP_VERSION", "2.0.0")

    @property
    def base_url(self) -> str:
        return os.getenv("BASE_URL", "http://localhost:8000")

    @property
    def debug(self) -> bool:
        return os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

    def __repr__(self) -> str:
        return f"<Settings app={self.app_name} v{self.app_version}>"


settings = _Settings()
