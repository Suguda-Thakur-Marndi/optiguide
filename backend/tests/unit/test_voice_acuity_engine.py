"""Unit tests for Voice-Controlled Adaptive Visual Acuity Engine.

Covers:
- Spoken letter and directional speech normalization.
- NATO phonetic alphabet and colloquial pronunciation mappings.
- Visual inability distinction from speech recognition failure.
- Ambiguity and low-confidence retry enforcement.
- Landolt C optotype generation and staircase integration.
"""

import pytest

from app.services.adaptive_acuity_engine import AdaptiveAcuityEngine, OptotypeType
from app.services.voice_acuity_interpreter import VoiceAcuityInterpreter

# ---------------------------------------------------------------------------
# 1. Tumbling E & Landolt C Directional Voice Interpretation Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_input,expected_direction",
    [
        ("up", "UP"),
        ("UP", "UP"),
        ("pointing up", "UP"),
        ("pointing upwards", "UP"),
        ("open up", "UP"),
        ("to the top", "UP"),
        ("down", "DOWN"),
        ("pointing down", "DOWN"),
        ("pointing downwards", "DOWN"),
        ("open down", "DOWN"),
        ("bottom", "DOWN"),
        ("left", "LEFT"),
        ("pointing left", "LEFT"),
        ("to the left", "LEFT"),
        ("open left", "LEFT"),
        ("right", "RIGHT"),
        ("pointing right", "RIGHT"),
        ("to the right", "RIGHT"),
        ("open right", "RIGHT"),
    ],
)
def test_directional_voice_recognition_tumbling_e(raw_input: str, expected_direction: str):
    """Verifies that spoken directions are accurately normalized for Tumbling E."""
    result = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript=raw_input,
        confidence=0.92,
        optotype_type="TUMBLING_E",
    )
    assert result.status == "RECOGNIZED"
    assert result.normalized_symbol == expected_direction
    assert result.retry_required is False


def test_directional_voice_recognition_landolt_c():
    """Verifies Landolt C directions are accurately normalized."""
    for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
        result = VoiceAcuityInterpreter.interpret_voice_response(
            raw_transcript=f"pointing {direction.lower()}",
            confidence=0.88,
            optotype_type="LANDOLT_C",
        )
        assert result.status == "RECOGNIZED"
        assert result.normalized_symbol == direction
        assert result.retry_required is False


# ---------------------------------------------------------------------------
# 2. Sloan Letters & NATO Phonetics Voice Interpretation Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_input,expected_letter",
    [
        ("C", "C"),
        ("see", "C"),
        ("charlie", "C"),
        ("D", "D"),
        ("delta", "D"),
        ("dee", "D"),
        ("E", "E"),
        ("echo", "E"),
        ("F", "F"),
        ("foxtrot", "F"),
        ("eff", "F"),
        ("L", "L"),
        ("lima", "L"),
        ("el", "L"),
        ("N", "N"),
        ("november", "N"),
        ("en", "N"),
        ("O", "O"),
        ("oscar", "O"),
        ("oh", "O"),
        ("P", "P"),
        ("papa", "P"),
        ("pee", "P"),
        ("T", "T"),
        ("tango", "T"),
        ("tee", "T"),
        ("Z", "Z"),
        ("zulu", "Z"),
        ("zee", "Z"),
        ("zed", "Z"),
    ],
)
def test_sloan_letter_and_nato_phonetic_recognition(raw_input: str, expected_letter: str):
    """Verifies standard 10 Sloan optotype letters and NATO phonetic pronunciations."""
    result = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript=raw_input,
        confidence=0.85,
        optotype_type="SLOAN",
    )
    assert result.status == "RECOGNIZED"
    assert result.normalized_symbol == expected_letter
    assert result.retry_required is False


def test_transcript_filler_phrase_cleaning():
    """Colloquial conversational fillers should be stripped before matching."""
    result = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript="I think it is pointing up",
        confidence=0.90,
        optotype_type="TUMBLING_E",
    )
    assert result.status == "RECOGNIZED"
    assert result.normalized_symbol == "UP"

    result_sloan = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript="The letter is charlie",
        confidence=0.95,
        optotype_type="SLOAN",
    )
    assert result_sloan.status == "RECOGNIZED"
    assert result_sloan.normalized_symbol == "C"


# ---------------------------------------------------------------------------
# 3. Clinical Visual Inability vs. Speech Uncertainty Separation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "phrase",
    [
        "cannot see",
        "can't see",
        "can not see",
        "i can't read it",
        "can't make it out",
        "don't know",
        "dont know",
        "too small",
        "too blurry",
        "blurry",
        "fuzzy",
        "no idea",
        "nothing",
        "blank",
    ],
)
def test_visual_inability_phrases_marked_cannot_see(phrase: str):
    """
    Phrases indicating the user visually cannot resolve the optotype must be
    scored as CANNOT_SEE without requiring retry or penalizing microphone/STT.
    """
    result = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript=phrase,
        confidence=0.91,
        optotype_type="TUMBLING_E",
    )
    assert result.status == "CANNOT_SEE"
    assert result.normalized_symbol == "CANNOT_SEE"
    assert result.retry_required is False


def test_empty_speech_requires_retry():
    """Silence or empty transcript triggers UNRECOGNIZED and retry_required."""
    result = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript="",
        confidence=0.0,
        optotype_type="TUMBLING_E",
    )
    assert result.status == "UNRECOGNIZED"
    assert result.retry_required is True
    assert "No speech detected" in result.feedback_message


def test_low_confidence_requires_retry():
    """Confidence below threshold triggers LOW_CONFIDENCE and retry_required."""
    result = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript="up",
        confidence=0.25,  # below 0.35 threshold
        optotype_type="TUMBLING_E",
    )
    assert result.status == "LOW_CONFIDENCE"
    assert result.retry_required is True
    assert "Audio was unclear" in result.feedback_message


def test_ambiguous_directional_speech():
    """Conflicting spoken directions triggers AMBIGUOUS and retry_required."""
    result = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript="it is pointing up or maybe down",
        confidence=0.88,
        optotype_type="TUMBLING_E",
    )
    assert result.status == "AMBIGUOUS"
    assert result.retry_required is True
    assert "Multiple directions detected" in result.feedback_message


def test_ambiguous_letter_speech():
    """Conflicting spoken letters triggers AMBIGUOUS and retry_required."""
    result = VoiceAcuityInterpreter.interpret_voice_response(
        raw_transcript="charlie or delta",
        confidence=0.89,
        optotype_type="SLOAN",
    )
    assert result.status == "AMBIGUOUS"
    assert result.retry_required is True
    assert "Multiple letters detected" in result.feedback_message


# ---------------------------------------------------------------------------
# 4. Landolt C Optotype Engine Support
# ---------------------------------------------------------------------------


def test_landolt_c_optotype_generation():
    """Verifies that Landolt C optotypes generate correct symbols and choices."""
    symbol, expected, choices = AdaptiveAcuityEngine.generate_next_optotype(
        optotype_type=OptotypeType.LANDOLT_C,
        previous_optotype=None,
    )
    assert symbol.startswith("C_")
    assert expected in ["UP", "DOWN", "LEFT", "RIGHT"]
    assert choices == ["UP", "DOWN", "LEFT", "RIGHT"]


def test_optotype_type_enum_supports_landolt_c():
    """OptotypeType enum must include LANDOLT_C."""
    assert OptotypeType.LANDOLT_C == "LANDOLT_C"
    assert OptotypeType.TUMBLING_E == "TUMBLING_E"
    assert OptotypeType.SLOAN == "SLOAN"
