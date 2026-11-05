"""OptiGuide Voice Assistant API Router.

Exposes endpoints for Speech-to-Text (STT), Text-to-Speech (TTS),
and End-to-End Voice Screening Guidance.
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile, status

from app.core.config import settings
from app.schemas.voice import (
    SynthesizeRequest,
    TranscriptionResponse,
    VoiceChatResponse,
    VoiceStatusResponse,
)
from app.services.voice_service import VoiceService

router = APIRouter()


@router.get(
    "/status",
    response_model=VoiceStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Voice Assistant Capability & Engine Status",
    description="Inspects operational health of STT, TTS, and offline capabilities.",
)
async def get_voice_status() -> VoiceStatusResponse:
    """Returns the operational status and engine configuration of the voice pipeline."""
    return VoiceStatusResponse(
        stt_status="ready" if settings.VOICE_ENABLED else "disabled",
        tts_status="ready" if settings.VOICE_ENABLED else "disabled",
        stt_provider=settings.VOICE_STT_PROVIDER,
        tts_provider=settings.VOICE_TTS_PROVIDER,
        offline_capable=True,
        supported_audio_formats=["audio/wav", ".wav"],
        max_upload_size_bytes=settings.VOICE_MAX_UPLOAD_SIZE_BYTES,
    )


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe Microphone Audio (Speech-to-Text)",
    description="Converts uploaded PCM WAV microphone audio into recognized text with confidence metrics.",
)
async def transcribe_audio(
    file: Annotated[
        UploadFile,
        File(description="PCM WAV audio recording from device microphone."),
    ],
) -> TranscriptionResponse:
    """Accepts and validates an audio file upload, performing speech-to-text recognition."""
    audio_bytes = await file.read()
    result = VoiceService.transcribe_audio(audio_bytes, filename=file.filename)
    return TranscriptionResponse(
        text=result.text,
        confidence=result.confidence,
        duration_seconds=result.duration_seconds,
        provider=result.provider,
    )


@router.post(
    "/synthesize",
    status_code=status.HTTP_200_OK,
    summary="Synthesize Text to Speech Audio (Text-to-Speech)",
    description="Converts clinical text guidance into playable spoken audio stream (WAV or MP3).",
    responses={
        200: {
            "content": {
                "audio/wav": {},
                "audio/mpeg": {},
            },
            "description": "Binary audio stream.",
        }
    },
)
async def synthesize_speech(payload: SynthesizeRequest) -> Response:
    """Synthesizes text into audio data and returns playable binary audio stream."""
    audio_bytes, media_type = VoiceService.synthesize_speech(
        text=payload.text,
        audio_format=payload.format,
        voice_id=payload.voice_id,
    )
    ext = "wav" if "wav" in media_type else "mp3"
    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f"inline; filename=optiguide_speech.{ext}",
            "Content-Length": str(len(audio_bytes)),
        },
    )


@router.post(
    "/chat",
    response_model=VoiceChatResponse,
    status_code=status.HTTP_200_OK,
    summary="End-to-End Voice Screening Dialogue",
    description="Processes microphone audio or text prompt through STT, Clinical Guidance Engine, and TTS.",
)
async def voice_chat(
    file: Annotated[
        UploadFile | None,
        File(description="Optional microphone audio recording (.wav)."),
    ] = None,
    text: Annotated[
        str | None,
        Form(description="Optional text prompt when testing without microphone."),
    ] = None,
) -> VoiceChatResponse:
    """Executes the complete voice pipeline: Speech-to-Text -> Dialogue Reasoning -> Text-to-Speech."""
    audio_bytes = await file.read() if file else None
    filename = file.filename if file else None

    result = VoiceService.execute_voice_chat(
        audio_bytes=audio_bytes,
        filename=filename,
        text_override=text,
    )

    return VoiceChatResponse(
        transcription=result.transcription,
        response_text=result.response_text,
        intent=result.intent,
        confidence=result.confidence,
        audio_base64=result.audio_base64,
        audio_format=result.audio_format,
        clinical_disclaimer=result.clinical_disclaimer,
    )
