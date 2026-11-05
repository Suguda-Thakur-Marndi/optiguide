"""OptiGuide Voice Assistant Service.

Provides Speech-to-Text (STT), Conversational Intent Guidance,
and Text-to-Speech (TTS) audio synthesis with clinical safety guardrails.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.exceptions import ValidationException
from app.core.logging import logger

CLINICAL_DISCLAIMER_TEXT = (
    "CLINICAL DISCLAIMER: OptiGuide voice assistant provides preliminary vision screening guidance and eyewear information. "
    "It does not provide medical diagnoses, treatment plans, or optical prescriptions. "
    "Consult a licensed eye care professional for comprehensive clinical evaluation."
)


@dataclass
class TranscriptionResult:
    text: str
    confidence: float | None
    duration_seconds: float | None
    provider: str


@dataclass
class VoiceGuidanceResult:
    response_text: str
    intent: str
    clinical_disclaimer: str


@dataclass
class VoiceChatResult:
    transcription: str
    response_text: str
    intent: str
    confidence: float | None
    audio_base64: str
    audio_format: str
    clinical_disclaimer: str


class VoiceService:
    """Core domain service for audio validation, STT, dialogue guidance, and TTS."""

    @staticmethod
    def validate_audio_file(audio_bytes: bytes, filename: str | None = None) -> float:
        """Validates that uploaded audio bytes conform to supported PCM WAV specifications.

        Returns audio duration in seconds on success, or raises ValidationException.
        """
        if not audio_bytes or len(audio_bytes) < 44:
            raise ValidationException(
                "Audio recording is empty or corrupt (insufficient byte length)."
            )

        if len(audio_bytes) > settings.VOICE_MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.VOICE_MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise ValidationException(
                f"Audio file exceeds maximum upload size limit ({max_mb} MB)."
            )

        # WAV Magic bytes check: 'RIFF....WAVE'
        if not (audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"):
            raise ValidationException(
                "Unsupported audio format. Audio must be a valid PCM WAV (.wav) file."
            )

        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
                nchannels = wav_file.getnchannels()
                sampwidth = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                nframes = wav_file.getnframes()

                if nframes == 0 or framerate == 0:
                    raise ValidationException(
                        "Audio file contains 0 audio frames (empty recording)."
                    )

                duration = nframes / float(framerate)
                if duration < 0.1:
                    raise ValidationException(
                        "Audio recording is too brief to contain intelligible speech (under 100ms)."
                    )

                logger.debug(
                    f"Validated WAV audio: {nchannels} ch, {sampwidth * 8}-bit, "
                    f"{framerate} Hz, {duration:.2f}s duration."
                )
                return duration
        except wave.Error as err:
            raise ValidationException(f"Corrupt or unreadable WAV audio header: {err}") from err

    @classmethod
    def transcribe_audio(
        cls, audio_bytes: bytes, filename: str | None = None
    ) -> TranscriptionResult:
        """Transcribes PCM WAV audio bytes into text using the local or configured STT provider."""
        duration = cls.validate_audio_file(audio_bytes, filename)

        # Write to temporary WAV file for recognizer processing
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            temp_path = tf.name

        try:
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)

            # Local Windows System.Speech.Recognition Engine (100% Offline)
            normalized_path = temp_path.replace("\\", "/")
            ps_script = (
                "& { "
                "Add-Type -AssemblyName System.Speech; "
                "$r = New-Object System.Speech.Recognition.SpeechRecognitionEngine; "
                f"$r.SetInputToWaveFile('{normalized_path}'); "
                "$d = New-Object System.Speech.Recognition.DictationGrammar; "
                "$r.LoadGrammar($d); "
                "$res = $r.Recognize(); "
                "if ($res) { "
                "  @{ text = $res.Text; confidence = [math]::Round($res.Confidence, 4) } | ConvertTo-Json -Compress "
                "} else { "
                "  @{ text = ''; confidence = 0.0 } | ConvertTo-Json -Compress "
                "}; "
                "$r.Dispose() "
                "}"
            )

            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                check=False,
                text=True,
                timeout=15,
            )

            if result.returncode != 0:
                logger.error(f"Speech recognition engine error: {result.stderr.strip()}")
                raise ValidationException(
                    "Speech recognition engine failed to process audio recording."
                )

            stdout_clean = result.stdout.strip()
            if not stdout_clean:
                return TranscriptionResult(
                    text="",
                    confidence=0.0,
                    duration_seconds=duration,
                    provider="windows_speech_api",
                )

            try:
                data: dict[str, Any] = json.loads(stdout_clean)
                recognized_text = data.get("text", "").strip()
                confidence = data.get("confidence")
                return TranscriptionResult(
                    text=recognized_text,
                    confidence=confidence,
                    duration_seconds=duration,
                    provider="windows_speech_api",
                )
            except json.JSONDecodeError:
                return TranscriptionResult(
                    text=stdout_clean,
                    confidence=None,
                    duration_seconds=duration,
                    provider="windows_speech_api",
                )

        except subprocess.TimeoutExpired as err:
            logger.error("Speech recognition timed out after 15 seconds.")
            raise ValidationException(
                "Speech recognition timed out while processing audio recording."
            ) from err
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    @classmethod
    def process_conversation_intent(cls, user_text: str) -> VoiceGuidanceResult:
        """Determines conversational intent and generates clinical guidance response.

        Clinical Safety Guardrail: Strictly refuses to prescribe eyewear or diagnose conditions.
        """
        clean_text = user_text.strip().lower()

        # 1. Emergency Triage Detection
        emergency_pattern = r"\b(pain\w*|hurts?|severe\w*|bleed\w*|trauma\w*|injur\w*|blind\w*|loss of vision|burn\w*|chemic\w*)\b"
        if re.search(emergency_pattern, clean_text):
            return VoiceGuidanceResult(
                response_text=(
                    "URGENT CLINICAL ALERT: If you are experiencing acute eye pain, sudden vision loss, "
                    "flashes of light, or physical trauma, please consult an emergency eye care specialist "
                    "or hospital emergency department immediately. OptiGuide is a non-diagnostic screening aid."
                ),
                intent="EMERGENCY_TRIAGE",
                clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
            )

        # 2. Visual Acuity Information (Specific module)
        acuity_pattern = (
            r"\b(visual acuity|acuity|optotype|snellen|tumbling e|eye chart|letter chart)\b"
        )
        if re.search(acuity_pattern, clean_text):
            return VoiceGuidanceResult(
                response_text=(
                    "The Visual Acuity screening measures how sharply you can distinguish symbols at a calibrated distance. "
                    "Optotypes such as the Tumbling E or Snellen letters will appear on your display. "
                    "You will be asked to identify their direction or letter while covering one eye at a time."
                ),
                intent="VISUAL_ACUITY_INFO",
                clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
            )

        # 3. Astigmatism Information (Specific module)
        astigmatism_pattern = r"\b(astigmatism|clock dial|dial|radiating lines|cylinder)\b"
        if re.search(astigmatism_pattern, clean_text):
            return VoiceGuidanceResult(
                response_text=(
                    "The Astigmatism screening uses a clock dial chart with radiating lines. "
                    "If certain lines appear noticeably darker, thicker, or sharper than others, "
                    "this may indicate astigmatic refractive variation across ocular meridians."
                ),
                intent="ASTIGMATISM_INFO",
                clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
            )

        # 4. Color Vision Information (Specific module)
        color_pattern = r"\b(color|colour|color vision|ishihara|plates|daltonism)\b"
        if re.search(color_pattern, clean_text):
            return VoiceGuidanceResult(
                response_text=(
                    "The Color Vision screening uses standardized Ishihara pseudoisochromatic plates. "
                    "You will identify numerals or trace pathways composed of dots with subtle chromatic variations. "
                    "Make sure your display brightness is normal and avoid colored lighting or heavy screen filters."
                ),
                intent="COLOR_VISION_INFO",
                clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
            )

        # 5. Pupillary Distance Information (Specific module)
        pd_pattern = r"\b(pupillary distance|pd|pupil distance|interpupillary)\b"
        if re.search(pd_pattern, clean_text):
            return VoiceGuidanceResult(
                response_text=(
                    "Pupillary distance (PD) is the distance between your pupil centers in millimeters. "
                    "Accurate pupillary distance ensures your optical center aligns with your spectacle lenses. "
                    "OptiGuide guides you through reference-card camera alignment for preliminary PD estimation."
                ),
                intent="PD_INFO",
                clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
            )

        # 6. Eyewear Guidance & Frames (Specific module)
        eyewear_pattern = r"\b(glasses|frames|spectacles|eyewear|catalogue|recommend|face shape)\b"
        if re.search(eyewear_pattern, clean_text):
            return VoiceGuidanceResult(
                response_text=(
                    "OptiGuide provides eyewear styling and frame recommendations based on facial morphology, "
                    "budget, and aesthetic preferences. Remember that corrective lens powers must be prescribed "
                    "by a licensed eye care professional following clinical refraction."
                ),
                intent="EYEWEAR_GUIDANCE",
                clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
            )

        # 7. Screening Start / Initiation (General action)
        start_pattern = r"\b(start|begin|initiate|test my eyes|screening|check vision|start screening|vision test)\b"
        if re.search(start_pattern, clean_text):
            return VoiceGuidanceResult(
                response_text=(
                    "Welcome to OptiGuide. We are ready to begin your preliminary vision screening. "
                    "The screening includes Visual Acuity, Astigmatism, and Color Vision assessments. "
                    "Please ensure your screen is at eye level in an evenly illuminated room, and keep any corrective "
                    "distance glasses on if instructed. Would you like to proceed with the Visual Acuity test?"
                ),
                intent="START_SCREENING",
                clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
            )

        # 8. Greetings & Help
        greeting_pattern = r"\b(hello|hi|hey|optiguide|help|good morning|good afternoon)\b"
        if re.search(greeting_pattern, clean_text):
            return VoiceGuidanceResult(
                response_text=(
                    "Hello! I am your OptiGuide assistant. I can guide you through preliminary vision screenings, "
                    "explain testing steps, and help you find suitable eyewear. How can I assist your vision journey today?"
                ),
                intent="GREETING",
                clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
            )

        # 9. General / Fallback
        return VoiceGuidanceResult(
            response_text=(
                f"You asked: '{user_text}'. OptiGuide is ready to assist you with preliminary vision screening, "
                "including Visual Acuity, Astigmatism, Color Vision tests, and eyewear frame guidance. "
                "How would you like to proceed?"
            ),
            intent="GENERAL_INQUIRY",
            clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
        )

    @classmethod
    def synthesize_speech(
        cls,
        text: str,
        audio_format: str = "wav",
        voice_id: str | None = None,
    ) -> tuple[bytes, str]:
        """Synthesizes text into spoken audio data.

        Supports 'wav' (local Windows SAPI offline) and 'mp3' (gTTS online).
        Returns tuple of (audio_bytes, media_type).
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValidationException("Text content for speech synthesis cannot be empty.")

        if len(clean_text) > 2000:
            raise ValidationException("Text content exceeds maximum limit of 2,000 characters.")

        # Format 1: WAV via Windows System.Speech.Synthesis (Offline, Fast)
        if audio_format.lower() == "wav" or settings.VOICE_TTS_PROVIDER == "local":
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                out_path = tf.name

            try:
                escaped_text = clean_text.replace("'", "''").replace('"', '`"')
                normalized_out = out_path.replace("\\", "/")
                ps_script = (
                    "& { "
                    "Add-Type -AssemblyName System.Speech; "
                    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.SetOutputToWaveFile('{normalized_out}'); "
                    f"$s.Speak('{escaped_text}'); "
                    "$s.Dispose() "
                    "}"
                )

                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command", ps_script],
                    capture_output=True,
                    check=False,
                    text=True,
                    timeout=15,
                )

                if result.returncode != 0:
                    logger.error(f"Windows TTS synthesis failed: {result.stderr.strip()}")
                    raise ValidationException("Text-to-Speech synthesis failed.")

                with open(out_path, "rb") as f:
                    audio_bytes = f.read()

                if len(audio_bytes) < 44:
                    raise ValidationException("Generated audio payload is empty or invalid.")

                return audio_bytes, "audio/wav"

            except subprocess.TimeoutExpired as err:
                raise ValidationException("TTS synthesis timed out.") from err
            finally:
                if os.path.exists(out_path):
                    try:
                        os.remove(out_path)
                    except OSError:
                        pass

        # Format 2: MP3 via gTTS (Online fallback)
        try:
            from gtts import gTTS

            tts = gTTS(text=clean_text, lang="en")
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            mp3_bytes = fp.getvalue()

            if not mp3_bytes:
                raise ValidationException("Generated MP3 audio payload is empty.")

            return mp3_bytes, "audio/mpeg"
        except (RuntimeError, OSError, ValueError, TypeError) as err:
            logger.warning(f"gTTS online synthesis failed ({err}), falling back to local SAPI WAV.")
            return cls.synthesize_speech(clean_text, audio_format="wav")

    @classmethod
    def execute_voice_chat(
        cls,
        audio_bytes: bytes | None = None,
        filename: str | None = None,
        text_override: str | None = None,
    ) -> VoiceChatResult:
        """Executes full end-to-end voice pipeline:

        Microphone Audio -> STT -> Dialogue Guidance -> TTS -> Audio Response.
        """
        # Step 1: Speech-to-Text or Direct Text
        if audio_bytes is not None:
            stt_result = cls.transcribe_audio(audio_bytes, filename)
            user_text = stt_result.text
            confidence = stt_result.confidence
        elif text_override and text_override.strip():
            user_text = text_override.strip()
            confidence = 1.0
        else:
            raise ValidationException("Either an audio recording or text prompt must be provided.")

        if not user_text:
            user_text = "Hello OptiGuide"
            confidence = 0.0

        # Step 2: Dialogue Processing & Clinical Intent Guidance
        guidance = cls.process_conversation_intent(user_text)

        # Step 3: Text-to-Speech Synthesis
        audio_response_bytes, media_type = cls.synthesize_speech(
            guidance.response_text, audio_format="wav"
        )

        audio_b64 = base64.b64encode(audio_response_bytes).decode("ascii")

        return VoiceChatResult(
            transcription=user_text,
            response_text=guidance.response_text,
            intent=guidance.intent,
            confidence=confidence,
            audio_base64=audio_b64,
            audio_format=media_type,
            clinical_disclaimer=guidance.clinical_disclaimer,
        )
