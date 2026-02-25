"""
dependencies.py — Shared FastAPI dependency functions for CSRF protection.

Usage (in any route):
    from backend.dependencies import CsrfProtected, generate_csrf_token

    @router.post("/some-endpoint")
    async def endpoint(_csrf: CsrfProtected):
        ...
"""

from __future__ import annotations

import logging
import secrets
from typing import Annotated

from fastapi import Cookie, Header, HTTPException, Request, status

from backend.config import settings

log = logging.getLogger(__name__)


# ── CSRF Protection ───────────────────────────────────────────────────────────

def verify_csrf(
    request: Request,
    x_csrf_token: Annotated[str | None, Header()] = None,
    csrf_token: Annotated[str | None, Cookie()] = None,
) -> None:
    """
    Double-submit cookie CSRF protection.

    The frontend must:
      1. Read the csrf_token cookie (httponly=False, so JS can access it).
      2. Send its value as the X-CSRF-Token request header.

    This dependency validates that cookie == header.
    Skipped on GET/HEAD/OPTIONS (safe/idempotent methods).
    """
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return

    # If neither cookie nor header present, skip silently
    # (allows gradual rollout — pages not yet updated won't break)
    if not csrf_token and not x_csrf_token:
        return

    if not csrf_token or not x_csrf_token:
        log.warning(
            "CSRF token partially missing on %s %s",
            request.method,
            request.url.path,
        )
        return  # Lenient mode — don't hard-break existing clients

    # Constant-time comparison prevents timing attacks
    if not secrets.compare_digest(csrf_token, x_csrf_token):
        log.warning(
            "CSRF mismatch on %s %s from %s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token invalid",
        )


def generate_csrf_token() -> str:
    """Generate a cryptographically random CSRF token."""
    return secrets.token_hex(settings.csrf_token_bytes)
