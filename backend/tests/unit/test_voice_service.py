"""Unit tests for OptiGuide Voice Assistant Service."""

import io
import wave

import pytest

from app.core.exceptions import ValidationException
from app.services.voice_service import CLINICAL_DISCLAIMER_TEXT, VoiceService


def _generate_synthetic_pcm_wav(duration_seconds: float = 1.0, framerate: int = 16000) -> bytes:
    """Helper to generate standard PCM 16-bit mono WAV bytes for testing."""
    buf = io.BytesIO()
    num_frames = int(duration_seconds * framerate)
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(framerate)
        wav.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


def test_validate_audio_file_valid():
    """Valid WAV bytes must return accurate duration in seconds."""
    wav_bytes = _generate_synthetic_pcm_wav(duration_seconds=1.5, framerate=16000)
    duration = VoiceService.validate_audio_file(wav_bytes, "test.wav")
    assert abs(duration - 1.5) < 0.05


def test_validate_audio_file_empty():
    """Empty or truncated audio data must raise ValidationException."""
    with pytest.raises(ValidationException, match="empty or corrupt"):
        VoiceService.validate_audio_file(b"")

    with pytest.raises(ValidationException, match="empty or corrupt"):
        VoiceService.validate_audio_file(b"RIFFshort")


def test_validate_audio_file_corrupt_non_wav():
    """Non-WAV binary data must be rejected."""
    fake_audio = b"NOT_A_WAV_FILE_HEADER_DATA_PADDING_BYTES_MORE_DATA"
    with pytest.raises(ValidationException, match="Audio must be a valid PCM WAV"):
        VoiceService.validate_audio_file(fake_audio, "fake.wav")


def test_validate_audio_file_oversized(monkeypatch):
    """Audio exceeding max upload size limit must be rejected."""
    monkeypatch.setattr("app.core.config.settings.VOICE_MAX_UPLOAD_SIZE_BYTES", 100)
    wav_bytes = _generate_synthetic_pcm_wav(duration_seconds=1.0)
    with pytest.raises(ValidationException, match="exceeds maximum upload size limit"):
        VoiceService.validate_audio_file(wav_bytes, "large.wav")


def test_validate_audio_file_zero_frames():
    """WAV with 0 frames must be rejected as empty recording."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        # 0 frames written
    with pytest.raises(ValidationException, match="0 audio frames"):
        VoiceService.validate_audio_file(buf.getvalue(), "empty.wav")


def test_intent_emergency_triage():
    """Emergency keywords must trigger urgent triage alert."""
    result = VoiceService.process_conversation_intent(
        "I have severe eye pain and sudden vision loss"
    )
    assert result.intent == "EMERGENCY_TRIAGE"
    assert "URGENT CLINICAL ALERT" in result.response_text
    assert result.clinical_disclaimer == CLINICAL_DISCLAIMER_TEXT


def test_intent_start_screening():
    """Screening initiation triggers welcome and flow guidance."""
    result = VoiceService.process_conversation_intent(
        "Hello OptiGuide, I want to start my vision screening."
    )
    assert result.intent == "START_SCREENING"
    assert "Visual Acuity" in result.response_text
    assert "preliminary vision screening" in result.response_text


def test_intent_visual_acuity_info():
    """Visual acuity inquiries return optotype protocol instructions."""
    result = VoiceService.process_conversation_intent(
        "How does the Snellen letter chart test work?"
    )
    assert result.intent == "VISUAL_ACUITY_INFO"
    assert "optotypes" in result.response_text.lower()


def test_intent_astigmatism_info():
    """Astigmatism inquiries return clock dial instructions."""
    result = VoiceService.process_conversation_intent(
        "Tell me about the astigmatism clock dial test"
    )
    assert result.intent == "ASTIGMATISM_INFO"
    assert "clock dial" in result.response_text.lower()


def test_intent_color_vision_info():
    """Color vision inquiries return Ishihara protocol instructions."""
    result = VoiceService.process_conversation_intent(
        "How is the Ishihara color vision screening performed?"
    )
    assert result.intent == "COLOR_VISION_INFO"
    assert "ishihara" in result.response_text.lower()


def test_intent_pd_info():
    """Pupillary distance inquiries return measurement guidance."""
    result = VoiceService.process_conversation_intent("How do you measure pupillary distance?")
    assert result.intent == "PD_INFO"
    assert "pupillary distance" in result.response_text.lower()


def test_intent_eyewear_guidance():
    """Eyewear inquiries return frame and styling advice with non-prescription disclaimer."""
    result = VoiceService.process_conversation_intent(
        "Can you recommend frames and glasses for my face shape?"
    )
    assert result.intent == "EYEWEAR_GUIDANCE"
    assert "eyewear styling" in result.response_text.lower()


def test_intent_greeting():
    """Greetings return welcoming assistant introduction."""
    result = VoiceService.process_conversation_intent("Hello OptiGuide")
    assert result.intent == "GREETING"
    assert "OptiGuide assistant" in result.response_text


def test_intent_general_fallback():
    """Unrecognized inquiries trigger safe general guidance."""
    result = VoiceService.process_conversation_intent("What is the weather outside today?")
    assert result.intent == "GENERAL_INQUIRY"
    assert "OptiGuide is ready to assist" in result.response_text


def test_synthesize_speech_offline_wav():
    """Synthesizing text produces valid, playable PCM WAV audio data."""
    text = "Hello from OptiGuide vision screening."
    audio_bytes, media_type = VoiceService.synthesize_speech(text, audio_format="wav")
    assert media_type == "audio/wav"
    assert len(audio_bytes) > 1000
    assert audio_bytes[:4] == b"RIFF"
    assert audio_bytes[8:12] == b"WAVE"


def test_synthesize_speech_empty_text():
    """Empty or whitespace-only text must raise ValidationException."""
    with pytest.raises(ValidationException, match="cannot be empty"):
        VoiceService.synthesize_speech("   ")


def test_synthesize_speech_oversized_text():
    """Text exceeding 2,000 characters must raise ValidationException."""
    long_text = "Vision " * 400
    with pytest.raises(ValidationException, match="exceeds maximum limit"):
        VoiceService.synthesize_speech(long_text)


def test_execute_voice_chat_text_override():
    """Executing voice chat with text returns complete guidance payload and base64 audio."""
    res = VoiceService.execute_voice_chat(text_override="I want to test my eyes")
    assert res.transcription == "I want to test my eyes"
    assert res.intent == "START_SCREENING"
    assert len(res.audio_base64) > 100
    assert res.audio_format == "audio/wav"
    assert res.clinical_disclaimer == CLINICAL_DISCLAIMER_TEXT


def test_execute_voice_chat_audio_file():
    """Executing voice chat with real synthetic WAV audio executes STT and TTS."""
    wav_bytes = _generate_synthetic_pcm_wav(duration_seconds=0.5)
    res = VoiceService.execute_voice_chat(audio_bytes=wav_bytes, filename="sample.wav")
    assert res.intent in ["GREETING", "GENERAL_INQUIRY", "START_SCREENING"]
    assert len(res.audio_base64) > 100
    assert res.audio_format == "audio/wav"
