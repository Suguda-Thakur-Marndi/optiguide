from backend.app.core.exceptions import (
    DatabaseConnectionException,
    EntityNotFoundException,
    OptiGuideException,
    ValidationException,
)


def test_custom_exceptions():
    base_ex = OptiGuideException("Base error", code="CUSTOM_CODE")
    assert str(base_ex) == "Base error"
    assert base_ex.code == "CUSTOM_CODE"

    not_found = EntityNotFoundException("Patient", "user-123")
    assert not_found.code == "NOT_FOUND"
    assert "user-123" in not_found.message

    val_ex = ValidationException("Invalid email format")
    assert val_ex.code == "VALIDATION_ERROR"

    db_ex = DatabaseConnectionException("Connection dropped")
    assert db_ex.code == "DATABASE_DISCONNECTED"
