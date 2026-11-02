import logging
import sys

from backend.app.core.config import settings

# Sensitive headers and parameter keys to sanitize
SENSITIVE_KEYS = {
    "authorization",
    "password",
    "token",
    "secret",
    "cookie",
    "access_token",
    "refresh_token",
    "api_key",
}


def sanitize_dict(data: dict) -> dict:
    """Recursively mask sensitive values in dictionaries."""
    sanitized = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        else:
            sanitized[k] = v
    return sanitized


def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Silence verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if not settings.DB_ECHO else logging.INFO
    )

    return logging.getLogger("optiguide")


logger = setup_logging()
