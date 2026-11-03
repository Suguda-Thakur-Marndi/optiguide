import hashlib
import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.screening import (
    ConsentAcceptRequest,
    ConsentStatusResponse,
    ScreeningSessionCancelRequest,
    ScreeningSessionCreateRequest,
    ScreeningSessionStatus,
)
from app.services.screening_service import (
    CONSENT_DOCUMENT_HASH,
    CONSENT_DOCUMENT_TEXT,
    CURRENT_CONSENT_VERSION,
)


def test_consent_text_hash_matches_official_content():
    calculated_hash = hashlib.sha256(CONSENT_DOCUMENT_TEXT.strip().encode("utf-8")).hexdigest()
    assert CONSENT_DOCUMENT_HASH == calculated_hash
    assert len(calculated_hash) == 64


def test_consent_accept_request_validation():
    # Valid
    req = ConsentAcceptRequest(version="1.0.0")
    assert req.version == "1.0.0"

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        ConsentAcceptRequest(version="1.0.0", is_active=True)


def test_screening_session_create_request_forbids_extra_fields():
    # Valid empty creation
    req = ScreeningSessionCreateRequest()
    assert req.model_dump() == {}

    # Client-supplied injected status forbidden
    with pytest.raises(ValidationError):
        ScreeningSessionCreateRequest(status="completed")

    # Client-supplied user_id injection forbidden
    with pytest.raises(ValidationError):
        ScreeningSessionCreateRequest(user_id=str(uuid.uuid4()))


def test_screening_session_cancel_request_validation():
    # Valid with reason
    req = ScreeningSessionCancelRequest(reason="User paused test")
    assert req.reason == "User paused test"

    # Valid with default None
    req_empty = ScreeningSessionCancelRequest()
    assert req_empty.reason is None

    # Length boundary (> 255 chars forbidden)
    long_reason = "X" * 256
    with pytest.raises(ValidationError):
        ScreeningSessionCancelRequest(reason=long_reason)


def test_screening_session_status_vocabulary():
    assert ScreeningSessionStatus.IN_PROGRESS.value == "in_progress"
    assert ScreeningSessionStatus.COMPLETED.value == "completed"
    assert ScreeningSessionStatus.CANCELLED.value == "cancelled"

    # Ensure disallowed medical diagnostic statuses are absent
    status_values = [s.value for s in ScreeningSessionStatus]
    assert "diagnosed" not in status_values
    assert "prescribed" not in status_values


def test_consent_status_response_serialization():
    res = ConsentStatusResponse(
        version=CURRENT_CONSENT_VERSION,
        title="Consent Title",
        content="Consent Content",
        hash=CONSENT_DOCUMENT_HASH,
        has_accepted=True,
        is_active=True,
        accepted_at=datetime.now(UTC),
    )
    assert res.version == "1.0.0"
    assert res.has_accepted is True
    assert res.is_active is True
