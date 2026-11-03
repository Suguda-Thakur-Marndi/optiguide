import io
import logging

from app.core.logging import SanitizingFilter, sanitize_dict, sanitize_log_message


def test_sanitize_dict_flat_and_case_insensitive():
    payload = {
        "username": "eyecare_admin",
        "PASSWORD": "PlaintextPassword123",
        "authorization": "Bearer eyJhbGciOi...",
        "api_key": "secret-api-key-value",
        "normal_field": "keep_this_intact",
    }
    sanitized = sanitize_dict(payload)
    assert sanitized["username"] == "eyecare_admin"
    assert sanitized["PASSWORD"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["normal_field"] == "keep_this_intact"


def test_sanitize_dict_nested_and_lists():
    payload = {
        "service": "optiguide-auth",
        "database": {
            "database_url": "postgresql+psycopg://user:pass@localhost:5432/db",
            "dsn": "host=localhost dbname=optiguide user=admin password=secret",
        },
        "sessions": [
            {"token": "token_1", "created_at": "2026-11-03"},
            {"token": "token_2", "created_at": "2026-11-03"},
        ],
    }
    sanitized = sanitize_dict(payload)
    assert sanitized["database"]["database_url"] == "[REDACTED]"
    assert sanitized["database"]["dsn"] == "[REDACTED]"
    assert sanitized["sessions"][0]["token"] == "[REDACTED]"
    assert sanitized["sessions"][0]["created_at"] == "2026-11-03"
    assert sanitized["sessions"][1]["token"] == "[REDACTED]"


def test_sanitize_log_message_credentials_in_url():
    raw_message = (
        "Failed to connect to database at "
        "postgresql+psycopg://optiguide_user:SuperSecretPassword!@10.0.1.50:5432/optiguide_prod"
    )
    sanitized = sanitize_log_message(raw_message)
    assert "SuperSecretPassword!" not in sanitized
    assert "optiguide_user:[REDACTED]@" in sanitized
    assert "10.0.1.50:5432/optiguide_prod" in sanitized


def test_sanitize_log_message_bearer_token():
    raw_message = "Authentication header was Bearer secret_jwt_token_value_abc123"
    sanitized = sanitize_log_message(raw_message)
    assert "secret_jwt_token_value_abc123" not in sanitized
    assert "Bearer [REDACTED]" in sanitized


def test_sanitizing_filter_in_logger():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(SanitizingFilter())
    handler.setFormatter(logging.Formatter("%(message)s"))

    test_logger = logging.getLogger("test_security_logger")
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(handler)

    test_logger.info(
        "Database failure: postgresql://admin:p@ssw0rd123@db.prod.internal:5432/optiguide"
    )
    output = stream.getvalue()
    assert "p@ssw0rd123" not in output
    assert "admin:[REDACTED]@" in output
