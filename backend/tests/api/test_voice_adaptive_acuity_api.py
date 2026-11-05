"""Integration tests for Voice-Controlled Adaptive Visual Acuity API.

Verifies:
- Initiating adaptive screening with LANDOLT_C, TUMBLING_E, and SLOAN.
- Submitting voice responses via JSON (base64) and multipart/form-data.
- Spoken letter and directional evaluation against server-side target.
- Ambiguity and low-confidence audio handling with non-penalizing retry requirement.
- Visual inability ("cannot see") scoring without speech retry.
- Complete adaptive voice test lifecycle with clinical assessment generation.
- Security isolation (IDOR protection, out-of-order sequence rejection).
"""

import base64
import io
import uuid
import wave

import pytest
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.models.screening_consent import ScreeningConsent
from app.models.screening_session import ScreeningSession
from app.models.user import User
from app.services.voice_service import TranscriptionResult, VoiceService


def _generate_synthetic_pcm_wav(duration_seconds: float = 1.0, framerate: int = 16000) -> bytes:
    """Generates valid standard PCM 16-bit mono WAV bytes for test payloads."""
    buf = io.BytesIO()
    num_frames = int(duration_seconds * framerate)
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(framerate)
        wav.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


@pytest.fixture
def test_subject(db_session) -> User:
    """Primary patient user."""
    user = User(
        email=f"voice_patient_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Voice Test Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_patient(db_session) -> User:
    """Secondary patient user for authorization testing."""
    user = User(
        email=f"voice_other_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="argon2id$mocked$hash",
        full_name="Other Voice Patient",
        role="patient",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def consented_session(db_session, test_subject) -> ScreeningSession:
    """Active consented screening session."""
    consent = ScreeningConsent(
        user_id=test_subject.id,
        consent_version="1.0.0",
        consent_text_hash="valid_consent_hash",
        is_active=True,
    )
    db_session.add(consent)
    db_session.commit()
    db_session.refresh(consent)

    session = ScreeningSession(
        user_id=test_subject.id,
        consent_id=consent.id,
        status="in_progress",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def _auth_headers(user: User) -> dict[str, str]:
    token, _ = create_access_token(user_id=user.id, email=user.email, role=user.role)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Start Adaptive Test with Landolt C
# ---------------------------------------------------------------------------


def test_start_adaptive_test_landolt_c(client: TestClient, test_subject, consented_session):
    """Starts adaptive test with Landolt C optotypes."""
    res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={
            "test_type": "DISTANCE",
            "test_eye": "right",
            "optotype_type": "LANDOLT_C",
            "starting_level": 6,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["optotype_type"] == "LANDOLT_C"
    assert data["presented_symbol"].startswith("C_")
    assert data["choices"] == ["UP", "DOWN", "LEFT", "RIGHT"]
    assert data["attempt_sequence"] == 1


# ---------------------------------------------------------------------------
# 2. Voice Response Submission via JSON (base64)
# ---------------------------------------------------------------------------


def test_voice_response_json_correct_advances(
    client: TestClient, test_subject, consented_session, monkeypatch
):
    """Submitting correct spoken answer via JSON base64 advances test."""
    # 1. Start test with Tumbling E
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={"test_type": "DISTANCE", "test_eye": "left", "optotype_type": "TUMBLING_E"},
    )
    assert start_res.status_code == 201
    test_id = start_res.json()["test_id"]
    symbol = start_res.json()["presented_symbol"]
    expected_direction = symbol.split("_")[1]  # E_UP -> UP

    # 2. Mock STT to return the expected direction
    monkeypatch.setattr(
        VoiceService,
        "transcribe_audio",
        lambda *args, **kwargs: TranscriptionResult(
            text=f"pointing {expected_direction.lower()}",
            confidence=0.94,
            duration_seconds=1.2,
            provider="System.Speech (test)",
        ),
    )

    wav_bytes = _generate_synthetic_pcm_wav(1.0)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    # 3. Submit voice response
    res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        headers=_auth_headers(test_subject),
        json={
            "attempt_sequence": 1,
            "audio_base64": b64_audio,
            "response_duration_ms": 1150,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["was_correct"] is True
    assert data["retry_required"] is False
    assert data["recognized_symbol"] == expected_direction
    assert data["input_modality"] == "VOICE"
    assert data["recognition_status"] == "RECOGNIZED"
    assert data["total_attempts"] == 1
    assert data["correct_attempts"] == 1
    assert data["next_challenge"] is not None
    assert data["next_challenge"]["attempt_sequence"] == 2


def test_voice_response_multipart_form_data(
    client: TestClient, test_subject, consented_session, monkeypatch
):
    """Submitting audio via multipart/form-data upload."""
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={"test_type": "DISTANCE", "test_eye": "right", "optotype_type": "SLOAN"},
    )
    test_id = start_res.json()["test_id"]
    expected_letter = start_res.json()["presented_symbol"]

    # Mock STT to return phonetic name e.g. "charlie" for C
    phonetic = "charlie" if expected_letter == "C" else expected_letter.lower()
    monkeypatch.setattr(
        VoiceService,
        "transcribe_audio",
        lambda *args, **kwargs: TranscriptionResult(
            text=f"the letter is {phonetic}",
            confidence=0.91,
            duration_seconds=1.0,
            provider="System.Speech (test)",
        ),
    )

    wav_bytes = _generate_synthetic_pcm_wav(1.0)

    res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        headers=_auth_headers(test_subject),
        data={"attempt_sequence": "1", "response_duration_ms": "950"},
        files={"file": ("recording.wav", wav_bytes, "audio/wav")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["retry_required"] is False
    assert data["input_modality"] == "VOICE"


# ---------------------------------------------------------------------------
# 3. Speech Uncertainty vs. Visual Inability
# ---------------------------------------------------------------------------


def test_voice_response_ambiguous_requires_retry(
    client: TestClient, test_subject, consented_session, monkeypatch
):
    """Ambiguous spoken responses prompt for retry without scoring attempt or advancing sequence."""
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={"test_type": "DISTANCE", "test_eye": "right", "optotype_type": "TUMBLING_E"},
    )
    test_id = start_res.json()["test_id"]

    # Mock ambiguous speech: "up or down"
    monkeypatch.setattr(
        VoiceService,
        "transcribe_audio",
        lambda *args, **kwargs: TranscriptionResult(
            text="it looks like up or maybe down",
            confidence=0.88,
            duration_seconds=1.5,
            provider="System.Speech (test)",
        ),
    )

    wav_bytes = _generate_synthetic_pcm_wav(1.0)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        headers=_auth_headers(test_subject),
        json={"attempt_sequence": 1, "audio_base64": b64_audio},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["retry_required"] is True
    assert data["recognition_status"] == "AMBIGUOUS"
    assert data["was_correct"] is None  # Not scored yet
    assert data["total_attempts"] == 0  # No penalty
    assert "Multiple directions detected" in data["feedback_message"]
    # Same challenge sequence is maintained
    assert data["next_challenge"]["attempt_sequence"] == 1


def test_voice_response_cannot_see_recorded_without_retry(
    client: TestClient, test_subject, consented_session, monkeypatch
):
    """
    When citizen speaks 'cannot see' or 'too blurry', it is recorded as an
    incorrect attempt without requiring microphone retry.
    """
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={"test_type": "DISTANCE", "test_eye": "left", "optotype_type": "TUMBLING_E"},
    )
    test_id = start_res.json()["test_id"]

    # Mock visual inability statement
    monkeypatch.setattr(
        VoiceService,
        "transcribe_audio",
        lambda *args, **kwargs: TranscriptionResult(
            text="I cannot see it, it is too blurry",
            confidence=0.92,
            duration_seconds=1.8,
            provider="System.Speech (test)",
        ),
    )

    wav_bytes = _generate_synthetic_pcm_wav(1.0)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        headers=_auth_headers(test_subject),
        json={"attempt_sequence": 1, "audio_base64": b64_audio},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["retry_required"] is False
    assert data["recognition_status"] == "CANNOT_SEE"
    assert data["was_correct"] is False
    assert data["total_attempts"] == 1
    assert data["correct_attempts"] == 0
    # Advances to attempt sequence 2
    assert data["next_challenge"]["attempt_sequence"] == 2


def test_voice_response_empty_audio_prompts_retry(
    client: TestClient, test_subject, consented_session
):
    """Submitting empty audio prompt triggers retry_required."""
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={"test_type": "DISTANCE", "test_eye": "right", "optotype_type": "TUMBLING_E"},
    )
    test_id = start_res.json()["test_id"]

    # Valid empty WAV bytes
    wav_bytes = _generate_synthetic_pcm_wav(0.5)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        headers=_auth_headers(test_subject),
        json={"attempt_sequence": 1, "audio_base64": b64_audio},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["retry_required"] is True
    assert data["recognition_status"] == "UNRECOGNIZED"


# ---------------------------------------------------------------------------
# 4. Full Voice Screening Lifecycle to Completion
# ---------------------------------------------------------------------------


def test_voice_controlled_test_full_progression_to_completion(
    client: TestClient, test_subject, consented_session, monkeypatch
):
    """
    Executes a complete adaptive screening run driven entirely by voice responses.
    Verifies test completion, score calculation, and clinical disclaimers.
    """
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={
            "test_type": "DISTANCE",
            "test_eye": "right",
            "optotype_type": "TUMBLING_E",
            "starting_level": 6,
        },
    )
    test_id = start_res.json()["test_id"]
    current_challenge = start_res.json()

    wav_bytes = _generate_synthetic_pcm_wav(0.5)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    is_complete = False
    result_data = None
    step_count = 0

    while not is_complete and step_count < 20:
        step_count += 1
        seq = current_challenge["attempt_sequence"]
        symbol = current_challenge["presented_symbol"]
        correct_direction = symbol.split("_")[1]

        cur_dir = correct_direction.lower()
        monkeypatch.setattr(
            VoiceService,
            "transcribe_audio",
            lambda *args, cur=cur_dir, **kwargs: TranscriptionResult(
                text=cur,
                confidence=0.95,
                duration_seconds=0.8,
                provider="System.Speech (test)",
            ),
        )

        resp = client.post(
            f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
            headers=_auth_headers(test_subject),
            json={"attempt_sequence": seq, "audio_base64": b64_audio},
        )
        assert resp.status_code == 200
        step_data = resp.json()
        is_complete = step_data["is_test_complete"]
        if is_complete:
            result_data = step_data["result_summary"]
            break
        current_challenge = step_data["next_challenge"]

    assert is_complete is True
    assert result_data is not None
    assert result_data["status"] == "COMPLETED"
    assert result_data["final_snellen"] is not None
    assert result_data["final_logmar"] is not None
    assert "preliminary functional assessment" in result_data["clinical_disclaimer"]
    assert "PRELIMINARY SCREENING" in result_data["validation_status"]


# ---------------------------------------------------------------------------
# 5. Security & Edge Case Handling
# ---------------------------------------------------------------------------


def test_voice_response_idor_forbidden(
    client: TestClient, test_subject, other_patient, consented_session
):
    """A user cannot submit a voice response to another patient's test."""
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={"test_type": "DISTANCE", "test_eye": "right", "optotype_type": "TUMBLING_E"},
    )
    test_id = start_res.json()["test_id"]

    wav_bytes = _generate_synthetic_pcm_wav(0.5)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        headers=_auth_headers(other_patient),
        json={"attempt_sequence": 1, "audio_base64": b64_audio},
    )
    assert res.status_code == 404


def test_voice_response_out_of_order_sequence_rejected(
    client: TestClient, test_subject, consented_session
):
    """Submitting an attempt sequence out of order must be rejected with 422."""
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={"test_type": "DISTANCE", "test_eye": "right", "optotype_type": "TUMBLING_E"},
    )
    test_id = start_res.json()["test_id"]

    wav_bytes = _generate_synthetic_pcm_wav(0.5)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        headers=_auth_headers(test_subject),
        json={"attempt_sequence": 999, "audio_base64": b64_audio},
    )
    assert res.status_code == 422
    assert "Out-of-order or duplicate attempt" in res.json()["error"]["message"]


def test_voice_response_invalid_audio_format_rejected(
    client: TestClient, test_subject, consented_session
):
    """Corrupt or non-WAV audio must be rejected with 422 Unprocessable Entity."""
    start_res = client.post(
        f"/api/v1/screening/sessions/{consented_session.id}/acuity/start",
        headers=_auth_headers(test_subject),
        json={"test_type": "DISTANCE", "test_eye": "right", "optotype_type": "TUMBLING_E"},
    )
    test_id = start_res.json()["test_id"]

    corrupt_audio_b64 = base64.b64encode(
        b"NOT_A_VALID_WAV_HEADER_OR_FILE_PADDING_DATA_LONGER_THAN_44_BYTES_LONG"
    ).decode("ascii")

    res = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        headers=_auth_headers(test_subject),
        json={"attempt_sequence": 1, "audio_base64": corrupt_audio_b64},
    )
    assert res.status_code == 422
    assert "Unsupported audio format" in res.json()["error"]["message"]
