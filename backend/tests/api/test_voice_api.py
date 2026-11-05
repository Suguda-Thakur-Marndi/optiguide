"""Integration API tests for OptiGuide Voice Assistant endpoints."""

import io
import wave


def _create_pcm_wav(duration: float = 0.5) -> bytes:
    """Creates in-memory PCM WAV bytes for API test uploads."""
    buf = io.BytesIO()
    framerate = 16000
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(framerate)
        wav.writeframes(b"\x00\x00" * int(duration * framerate))
    return buf.getvalue()


def test_get_voice_status(client):
    """GET /api/v1/voice/status must return operational capability report."""
    response = client.get("/api/v1/voice/status")
    assert response.status_code == 200
    data = response.json()
    assert data["stt_status"] == "ready"
    assert data["tts_status"] == "ready"
    assert data["offline_capable"] is True
    assert "audio/wav" in data["supported_audio_formats"]
    assert data["max_upload_size_bytes"] > 0


def test_synthesize_speech_api_success(client):
    """POST /api/v1/voice/synthesize returns playable binary audio stream."""
    payload = {"text": "Hello citizen, welcome to your vision screening session.", "format": "wav"}
    response = client.post("/api/v1/voice/synthesize", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert "optiguide_speech.wav" in response.headers["content-disposition"]
    audio_content = response.content
    assert len(audio_content) > 1000
    assert audio_content[:4] == b"RIFF"
    assert audio_content[8:12] == b"WAVE"


def test_synthesize_speech_api_empty_text(client):
    """POST /api/v1/voice/synthesize with empty text must fail with 422."""
    payload = {"text": "", "format": "wav"}
    response = client.post("/api/v1/voice/synthesize", json=payload)
    assert response.status_code == 422


def test_transcribe_audio_api_success(client):
    """POST /api/v1/voice/transcribe accepts valid WAV and returns transcription structure."""
    wav_bytes = _create_pcm_wav(duration=0.5)
    files = {"file": ("test_sample.wav", wav_bytes, "audio/wav")}
    response = client.post("/api/v1/voice/transcribe", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "provider" in data
    assert data["duration_seconds"] is not None


def test_transcribe_audio_api_invalid_file(client):
    """POST /api/v1/voice/transcribe with non-WAV data returns validation error."""
    files = {"file": ("corrupt.wav", b"INVALID_NON_WAV_BYTES_DATA", "audio/wav")}
    response = client.post("/api/v1/voice/transcribe", files=files)
    assert response.status_code in [400, 422]


def test_voice_chat_api_text_flow(client):
    """POST /api/v1/voice/chat with text returns complete guidance and base64 audio."""
    form_data = {"text": "Hello OptiGuide, I want to start my vision screening"}
    response = client.post("/api/v1/voice/chat", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "START_SCREENING"
    assert "Visual Acuity" in data["response_text"]
    assert len(data["audio_base64"]) > 100
    assert data["audio_format"] == "audio/wav"
    assert "CLINICAL DISCLAIMER" in data["clinical_disclaimer"]


def test_voice_chat_api_emergency_flow(client):
    """POST /api/v1/voice/chat with acute symptom returns emergency triage response."""
    form_data = {"text": "My eye hurts severely with sudden vision loss"}
    response = client.post("/api/v1/voice/chat", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "EMERGENCY_TRIAGE"
    assert "URGENT CLINICAL ALERT" in data["response_text"]


def test_voice_chat_api_audio_flow(client):
    """POST /api/v1/voice/chat with audio file executes end-to-end voice pipeline."""
    wav_bytes = _create_pcm_wav(duration=0.5)
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    response = client.post("/api/v1/voice/chat", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data
    assert "response_text" in data
    assert len(data["audio_base64"]) > 100


def test_voice_chat_api_missing_inputs(client):
    """POST /api/v1/voice/chat with neither audio nor text returns validation error."""
    response = client.post("/api/v1/voice/chat")
    assert response.status_code in [400, 422]
