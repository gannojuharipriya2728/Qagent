"""
Helpers for turning exceptions into messages that are safe to return to a client.

Driver-level exceptions routinely embed the thing that failed to connect, which
for us means the Neon connection string or an upstream ``Authorization`` header.
Anything travelling back over HTTP goes through :func:`safe_error_detail` first.
"""

import logging
from typing import Iterable

from app.core.config import settings

logger = logging.getLogger("qagent.errors")

REDACTED = "[REDACTED]"
MAX_DETAIL_LENGTH = 300


def _secret_values() -> Iterable[str]:
    candidates = [
        settings.SECRET_KEY,
        getattr(settings, "OPENROUTER_API_KEY", ""),
        getattr(settings, "NVIDIA_API_KEY", ""),
        getattr(settings, "S3_SECRET_ACCESS_KEY", ""),
        getattr(settings, "S3_ACCESS_KEY_ID", ""),
        getattr(settings, "DATABASE_URL", ""),
    ]
    for value in candidates:
        if value and len(str(value)) > 4:
            yield str(value)


def redact_secrets(message: str) -> str:
    """Replaces any configured secret that appears verbatim in ``message``."""
    for secret in _secret_values():
        message = message.replace(secret, REDACTED)
    return message


def safe_error_detail(exc: BaseException, fallback: str = "Internal server error.") -> str:
    """
    Produces a short, secret-free description of ``exc`` for an HTTP response.

    The full exception (with traceback) still reaches the service logs via the
    caller's ``logger.exception``; only the client-facing string is trimmed.
    """
    raw = str(exc).strip()
    if not raw:
        return f"{exc.__class__.__name__}: {fallback}"

    first_line = raw.splitlines()[0]
    cleaned = redact_secrets(first_line)
    if len(cleaned) > MAX_DETAIL_LENGTH:
        cleaned = cleaned[:MAX_DETAIL_LENGTH].rstrip() + "…"
    return cleaned
