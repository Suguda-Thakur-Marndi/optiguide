import logging
import re
import sys
from typing import Any

from app.core.config import settings

# Substrings indicating sensitive keys in dictionaries or headers
SENSITIVE_KEY_SUBSTRINGS = {
    "authorization",
    "password",
    "token",
    "secret",
    "cookie",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "private_key",
    "secret_key",
    "database_url",
    "db_url",
    "dsn",
    "connection_string",
}

# Regex patterns for sanitizing connection strings, credentials and tokens in text
URL_CREDENTIAL_PATTERN = re.compile(
    r"(://[^:\s]+:)([^@\s]+)(@)",
    re.IGNORECASE,
)
KEY_VALUE_SECRET_PATTERN = re.compile(
    r"((?:password|token|secret|api_key|access_token|refresh_token)\s*[:=]\s*)(['\"]?[^\s,'\"]+['\"]?)",
    re.IGNORECASE,
)
BEARER_TOKEN_PATTERN = re.compile(
    r"(Bearer\s+)([A-Za-z0-9\-._~+/]+=*)",
    re.IGNORECASE,
)


def sanitize_dict(data: dict) -> dict:
    """Recursively mask sensitive values in dictionaries and nested structures."""
    sanitized: dict[str, Any] = {}
    for k, v in data.items():
        k_str = str(k).lower()
        if any(sub in k_str for sub in SENSITIVE_KEY_SUBSTRINGS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_dict(item) if isinstance(item, dict) else item for item in v]
        elif isinstance(v, tuple):
            sanitized[k] = tuple(
                sanitize_dict(item) if isinstance(item, dict) else item for item in v
            )
        else:
            sanitized[k] = v
    return sanitized


def sanitize_log_message(message: str) -> str:
    """Sanitizes raw log messages, stripping URLs with credentials and token values."""
    if not isinstance(message, str):
        return message
    sanitized = URL_CREDENTIAL_PATTERN.sub(r"\1[REDACTED]\3", message)
    sanitized = KEY_VALUE_SECRET_PATTERN.sub(r"\1[REDACTED]", sanitized)
    sanitized = BEARER_TOKEN_PATTERN.sub(r"\1[REDACTED]", sanitized)
    return sanitized


class SanitizingFilter(logging.Filter):
    """Logging filter that redacts credentials, URLs and tokens from emitted log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    sanitize_log_message(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


def setup_logging() -> logging.Logger:
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SanitizingFilter())

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[handler],
        force=True,
    )

    # Silence verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if not settings.DB_ECHO else logging.INFO
    )

    app_logger = logging.getLogger("optiguide")
    app_logger.addFilter(SanitizingFilter())
    return app_logger


logger = setup_logging()
