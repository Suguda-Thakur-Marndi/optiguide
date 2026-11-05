"""Pydantic schemas for OptiGuide Voice Assistant and Audio Processing."""

from pydantic import BaseModel, ConfigDict, Field


class TranscriptionResponse(BaseModel):
    """Result of Speech-to-Text transcription."""

    model_config = ConfigDict(extra="ignore")

    text: str = Field(..., description="Recognized spoken text from microphone audio.")
    confidence: float | None = Field(
        None, description="Recognition confidence score between 0.0 and 1.0."
    )
    duration_seconds: float | None = Field(
        None, description="Duration of processed audio in seconds."
    )
    provider: str = Field(..., description="STT engine used for transcription.")


class SynthesizeRequest(BaseModel):
    """Request payload for Text-to-Speech synthesis."""

    model_config = ConfigDict(extra="ignore")

    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Text content to be synthesized into spoken audio.",
    )
    format: str = Field(
        "wav",
        pattern="^(wav|mp3)$",
        description="Requested audio format: 'wav' (uncompressed PCM) or 'mp3'.",
    )
    voice_id: str | None = Field(None, description="Optional voice identifier.")


class VoiceChatResponse(BaseModel):
    """End-to-End Voice Conversation response."""

    model_config = ConfigDict(extra="ignore")

    transcription: str = Field(..., description="User spoken text recognized via STT.")
    response_text: str = Field(..., description="OptiGuide assistant clinical guidance response.")
    intent: str = Field(..., description="Categorized conversation intent.")
    confidence: float | None = Field(None, description="STT recognition confidence score.")
    audio_base64: str = Field(..., description="Base64-encoded synthesized response audio.")
    audio_format: str = Field(..., description="Audio MIME content type (audio/wav or audio/mpeg).")
    clinical_disclaimer: str = Field(..., description="Mandatory clinical safety disclaimer.")


class VoiceStatusResponse(BaseModel):
    """Status report of backend voice and audio capabilities."""

    model_config = ConfigDict(extra="ignore")

    stt_status: str = Field(..., description="Operating status of STT engine.")
    tts_status: str = Field(..., description="Operating status of TTS engine.")
    stt_provider: str = Field(..., description="Active STT provider name.")
    tts_provider: str = Field(..., description="Active TTS provider name.")
    offline_capable: bool = Field(
        ..., description="Whether voice pipeline operates without internet connection."
    )
    supported_audio_formats: list[str] = Field(
        ..., description="List of accepted audio upload formats."
    )
    max_upload_size_bytes: int = Field(..., description="Maximum audio file upload size in bytes.")
