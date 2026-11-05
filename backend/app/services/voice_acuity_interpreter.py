"""Voice-Controlled Visual Acuity Response Interpreter.

Safely normalizes spoken citizen responses into canonical optotype answers (directions
or letters) or detects speech recognition uncertainty, background noise, ambiguity,
or visual inability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class VoiceInterpretationResult:
    """Outcome of interpreting transcribed audio for visual acuity testing."""

    status: str  # 'RECOGNIZED', 'CANNOT_SEE', 'LOW_CONFIDENCE', 'AMBIGUOUS', 'UNRECOGNIZED', 'INVALID_AUDIO'
    normalized_symbol: str | None
    raw_transcript: str
    confidence: float | None
    retry_required: bool
    feedback_message: str


class VoiceAcuityInterpreter:
    """Clinical speech normalization and ambiguity resolution for acuity testing."""

    MIN_CONFIDENCE_THRESHOLD: float = 0.35

    # Visual inability indicator phrases (distinguished from STT failure)
    VISUAL_INABILITY_PATTERNS: ClassVar[list[str]] = [
        r"\b(can'?t|cannot|can not)\s+(.*?\s+)?(see|read|make\s+(it\s+)?out|distinguish|tell)\b",
        r"\b(don'?t|dont)\s+know\b",
        r"\b(not\s+visible|too\s+small|too\s+blurry|blurry|blur|fuzzy|unclear)\b",
        r"\b(no\s+idea|nothing|blank)\b",
    ]

    # Tumbling E / Landolt C directional regexes
    DIRECTION_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "UP": [
            r"\b(pointing\s+)?up(wards?|ward)?\b",
            r"\b(top|open\s+up|pointing\s+to\s+the\s+top)\b",
        ],
        "DOWN": [
            r"\b(pointing\s+)?down(wards?|ward)?\b",
            r"\b(bottom|open\s+down|pointing\s+to\s+the\s+bottom)\b",
        ],
        "LEFT": [
            r"\b(pointing\s+)?left(wards?|ward)?\b",
            r"\b(open\s+left|to\s+the\s+left|towards\s+left)\b",
        ],
        "RIGHT": [
            r"\b(pointing\s+)?right(wards?|ward)?\b",
            r"\b(open\s+right|to\s+the\s+right|towards\s+right)\b",
        ],
    }

    # Sloan letter pronunciations and NATO phonetic equivalents
    LETTER_MAPPINGS: ClassVar[dict[str, list[str]]] = {
        # Standard 10 Sloan Letters (NAS-NRC / ISO 8596)
        "C": [r"\b(c|see|sea|charlie)\b"],
        "D": [r"\b(d|dee|delta)\b"],
        "E": [r"\b(e|ee|echo)\b"],
        "F": [r"\b(f|eff|foxtrot)\b"],
        "L": [r"\b(l|el|ell|lima)\b"],
        "N": [r"\b(n|en|enn|november)\b"],
        "O": [r"\b(o|oh|zero|oscar)\b"],
        "P": [r"\b(p|pee|papa)\b"],
        "T": [r"\b(t|tee|tea|tango)\b"],
        "Z": [r"\b(z|zee|zed|zulu)\b"],
        # Other letters citizen might misidentify the optotype as
        "A": [r"\b(a|ay|alpha)\b"],
        "B": [r"\b(b|bee|bravo)\b"],
        "G": [r"\b(g|gee|golf)\b"],
        "H": [r"\b(h|aitch|hotel)\b"],
        "I": [r"\b(i|eye|india)\b"],
        "J": [r"\b(j|jay|juliet)\b"],
        "K": [r"\b(k|kay|kilo)\b"],
        "M": [r"\b(m|em|mike)\b"],
        "Q": [r"\b(q|cue|quebec)\b"],
        "R": [r"\b(r|ar|romeo)\b"],
        "S": [r"\b(s|ess|sierra)\b"],
        "U": [r"\b(u|you|uniform)\b"],
        "V": [r"\b(v|vee|victor)\b"],
        "W": [r"\b(w|double\s+u|whiskey)\b"],
        "X": [r"\b(x|ex|xray|x-ray)\b"],
        "Y": [r"\b(y|why|yankee)\b"],
    }

    @classmethod
    def clean_transcript(cls, text: str) -> str:
        """Strips filler words, punctuation, and normalizes casing."""
        if not text:
            return ""
        # Lowercase and remove punctuation except hyphens
        cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
        # Remove filler phrases e.g. "i think it is", "it looks like", "letter"
        fillers = [
            r"\b(i\s+think\s+it\s+is|it\s+looks\s+like|i\s+see|the\s+letter\s+is|the\s+letter|it\s+is|it's|is)\b"
        ]
        for f in fillers:
            cleaned = re.sub(f, " ", cleaned)
        return " ".join(cleaned.split())

    @classmethod
    def interpret_voice_response(
        cls,
        raw_transcript: str,
        confidence: float | None = None,
        optotype_type: str = "TUMBLING_E",
        min_confidence: float = MIN_CONFIDENCE_THRESHOLD,
    ) -> VoiceInterpretationResult:
        """Evaluates raw speech recognition against clinical optotype specifications.

        Distinguishes speech-recognition failure from visual inability.
        """
        raw = raw_transcript.strip() if raw_transcript else ""

        # 1. Empty Audio or Silence
        if not raw:
            return VoiceInterpretationResult(
                status="UNRECOGNIZED",
                normalized_symbol=None,
                raw_transcript="",
                confidence=confidence,
                retry_required=True,
                feedback_message="No speech detected. Please speak clearly into the microphone.",
            )

        # 2. Low Confidence Recognition
        if confidence is not None and confidence < min_confidence:
            return VoiceInterpretationResult(
                status="LOW_CONFIDENCE",
                normalized_symbol=None,
                raw_transcript=raw,
                confidence=confidence,
                retry_required=True,
                feedback_message="Audio was unclear. Please speak closer to the microphone and repeat your answer.",
            )

        cleaned = cls.clean_transcript(raw)

        # 3. Visual Inability Phrases (Clinically evaluated as unable to resolve)
        for pattern in cls.VISUAL_INABILITY_PATTERNS:
            if re.search(pattern, raw.lower()):
                return VoiceInterpretationResult(
                    status="CANNOT_SEE",
                    normalized_symbol="CANNOT_SEE",
                    raw_transcript=raw,
                    confidence=confidence,
                    retry_required=False,
                    feedback_message="Recorded: optotype could not be resolved.",
                )

        t = optotype_type.upper().strip()

        # 4. Tumbling E or Landolt C (Directional optotypes)
        if t in ["TUMBLING_E", "LANDOLT_C"]:
            detected: list[str] = []
            for direction, patterns in cls.DIRECTION_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, cleaned):
                        if direction not in detected:
                            detected.append(direction)
                        break

            if len(detected) > 1:
                return VoiceInterpretationResult(
                    status="AMBIGUOUS",
                    normalized_symbol=None,
                    raw_transcript=raw,
                    confidence=confidence,
                    retry_required=True,
                    feedback_message=(
                        f"Multiple directions detected ({', '.join(detected)}). "
                        "Please say only one direction (Up, Down, Left, or Right)."
                    ),
                )
            if len(detected) == 1:
                return VoiceInterpretationResult(
                    status="RECOGNIZED",
                    normalized_symbol=detected[0],
                    raw_transcript=raw,
                    confidence=confidence,
                    retry_required=False,
                    feedback_message=f"Recognized direction: {detected[0]}.",
                )

            return VoiceInterpretationResult(
                status="UNRECOGNIZED",
                normalized_symbol=None,
                raw_transcript=raw,
                confidence=confidence,
                retry_required=True,
                feedback_message="Direction not recognized. Please clearly say 'Up', 'Down', 'Left', or 'Right'.",
            )

        # 5. Sloan Letters (Character-based optotypes)
        detected_letters: list[str] = []
        for letter, patterns in cls.LETTER_MAPPINGS.items():
            for pat in patterns:
                if re.search(pat, cleaned):
                    if letter not in detected_letters:
                        detected_letters.append(letter)
                    break

        if len(detected_letters) > 1:
            return VoiceInterpretationResult(
                status="AMBIGUOUS",
                normalized_symbol=None,
                raw_transcript=raw,
                confidence=confidence,
                retry_required=True,
                feedback_message=(
                    f"Multiple letters detected ({', '.join(detected_letters)}). "
                    "Please speak only one letter."
                ),
            )
        if len(detected_letters) == 1:
            return VoiceInterpretationResult(
                status="RECOGNIZED",
                normalized_symbol=detected_letters[0],
                raw_transcript=raw,
                confidence=confidence,
                retry_required=False,
                feedback_message=f"Recognized letter: {detected_letters[0]}.",
            )

        return VoiceInterpretationResult(
            status="UNRECOGNIZED",
            normalized_symbol=None,
            raw_transcript=raw,
            confidence=confidence,
            retry_required=True,
            feedback_message="Letter not recognized. Please say the letter clearly (e.g. 'C', 'D', 'E').",
        )
