import pytest
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.error import ApiErrorPayload, ErrorDetail, ErrorResponse
from backend.app.schemas.health import AppInfoResponse, DatabaseHealthResponse, HealthResponse
from pydantic import ValidationError


def test_app_info_schema():
    info = AppInfoResponse(
        name="OptiGuide API", version="1.0.0", status="running", environment="test"
    )
    assert info.name == "OptiGuide API"
    assert info.status == "running"


def test_health_response_schema():
    health = HealthResponse(status="ok", service="optiguide-api", version="1.0.0")
    assert health.status == "ok"
    assert health.service == "optiguide-api"


def test_database_health_response_schema():
    db_health = DatabaseHealthResponse(status="ok", database="connected", latency_ms=1.5)
    assert db_health.status == "ok"
    assert db_health.database == "connected"
    assert db_health.latency_ms == 1.5


def test_error_envelope_schema():
    detail = ErrorDetail(loc=["body", "test"], msg="Field required", type="missing")
    payload = ApiErrorPayload(
        code="VALIDATION_ERROR", message="Validation failed", details=[detail]
    )
    envelope = ErrorResponse(error=payload)
    assert envelope.error.code == "VALIDATION_ERROR"
    assert len(envelope.error.details) == 1
    assert envelope.error.details[0].msg == "Field required"


def test_paginated_response_schema():
    page = PaginatedResponse[str](items=["item1", "item2"], total=2, page=1, page_size=10)
    assert page.total == 2
    assert len(page.items) == 2


def test_invalid_health_schema_raises():
    with pytest.raises(ValidationError):
        # Missing required 'service' and 'version'
        HealthResponse(status="ok")
