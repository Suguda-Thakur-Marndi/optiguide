import uuid
from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CalibrationInput(BaseModel):
    """Client-provided physical hardware and distance telemetry."""

    screen_width_px: int | None = Field(default=None, ge=100)
    screen_height_px: int | None = Field(default=None, ge=100)
    display_dpi: float | None = Field(default=None, ge=50.0, le=1200.0)
    viewing_distance_cm: float | None = Field(default=None, ge=20.0, le=1200.0)
    calibration_method: str | None = Field(
        default="client_unverified",
        description="Method used for calibration (e.g. 'reference_card', 'ar_depth_sensor', 'manual_ruler').",
    )
    is_professionally_supervised: bool = False

    model_config = ConfigDict(extra="ignore")


class AdaptiveAcuityStartRequest(BaseModel):
    """Payload to initiate an interactive, adaptive visual acuity test."""

    test_type: str = Field(
        default="DISTANCE",
        pattern="^(DISTANCE|NEAR|distance|near)$",
        description="DISTANCE (default) or NEAR test.",
    )
    test_eye: str = Field(
        ...,
        validation_alias=AliasChoices("test_eye", "tested_eye", "eye"),
        pattern="^(right|left|both|od|os|ou|right_eye|left_eye|both_eyes|RIGHT|LEFT|BOTH|OD|OS|OU|RIGHT_EYE|LEFT_EYE|BOTH_EYES)$",
        description="Eye tested: right (OD), left (OS), or both (OU).",
    )
    optotype_type: str = Field(
        default="TUMBLING_E",
        pattern="^(TUMBLING_E|SLOAN|LANDOLT_C|tumbling_e|sloan|landolt_c)$",
        description="Optotype set: TUMBLING_E (directions), SLOAN (10-letter set), or LANDOLT_C.",
    )
    protocol_version: str = Field(
        default="ISO8596_ATS_V1",
        description="Clinical staircase screening protocol version.",
    )
    starting_level: int = Field(
        default=6,
        ge=0,
        le=10,
        description="Initial difficulty level (0 = 20/200, 6 = 20/40 driving standard).",
    )
    viewing_distance_meters: float | None = Field(
        default=None,
        gt=0.2,
        le=12.0,
        description="Physical viewing distance in meters (defaults to 3.0m for distance, 0.4m for near).",
    )
    user_reported_occlusion: bool = Field(
        default=True,
        description="Citizen acknowledgment that non-tested eye is occluded correctly.",
    )
    calibration: CalibrationInput | None = None

    model_config = ConfigDict(extra="ignore")


class OptotypeChallengeResponse(BaseModel):
    """Client challenge specification. Never leaks expected response."""

    test_id: uuid.UUID
    attempt_sequence: int
    current_level: int
    level_snellen: str
    level_logmar: float
    optotype_type: str
    presented_symbol: str
    choices: list[str]
    target_size_arcmin: float
    target_height_mm: float | None = None
    target_height_px: float | None = None
    test_eye: str
    test_type: str
    instructions: str

    model_config = ConfigDict(from_attributes=True)


class AdaptiveAcuityResponseRequest(BaseModel):
    """Payload for submitting user's answer to the active optotype presentation."""

    attempt_sequence: int = Field(
        ..., ge=1, description="Sequence number of challenge being answered."
    )
    user_response: str = Field(
        ..., min_length=1, max_length=20, description="User selected direction or letter."
    )
    response_duration_ms: int | None = Field(
        default=None, ge=0, le=60000, description="Citizen response latency in milliseconds."
    )

    model_config = ConfigDict(extra="ignore")


class AdaptiveAcuityResultResponse(BaseModel):
    """Full preliminary screening result and clinical non-diagnostic determination."""

    test_id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    test_type: str
    test_eye: str
    optotype_type: str
    protocol_version: str
    status: str
    calibration_status: str
    is_calibrated: bool
    viewing_distance_meters: float
    user_reported_occlusion: bool
    total_attempts: int
    correct_attempts: int
    incorrect_attempts: int
    smallest_resolved_level: int | None = None
    final_snellen: str | None = None
    final_logmar: float | None = None
    final_decimal: float | None = None
    assessment_id: uuid.UUID | None = None
    started_at: datetime
    completed_at: datetime | None = None
    clinical_disclaimer: str
    validation_status: str

    model_config = ConfigDict(from_attributes=True)


class AdaptiveAcuityStepResponse(BaseModel):
    """Immediate outcome of a response submission with the next server-determined step."""

    test_id: uuid.UUID
    attempt_sequence: int
    test_status: str
    was_correct: bool
    level: int
    total_attempts: int
    correct_attempts: int
    is_test_complete: bool
    next_challenge: OptotypeChallengeResponse | None = None
    result_summary: AdaptiveAcuityResultResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class AdaptiveAcuityCancelRequest(BaseModel):
    """Cancellation payload."""

    reason: str | None = Field(default="user_cancelled", max_length=255)

    model_config = ConfigDict(extra="ignore")


class AdaptiveAcuityVoiceResponseRequest(BaseModel):
    """Payload for submitting base64 encoded audio or voice response telemetry."""

    attempt_sequence: int = Field(
        ..., ge=1, description="Sequence number of challenge being answered."
    )
    audio_base64: str | None = Field(
        default=None, description="Base64-encoded PCM WAV microphone recording."
    )
    response_duration_ms: int | None = Field(
        default=None, ge=0, le=60000, description="Citizen response latency in milliseconds."
    )

    model_config = ConfigDict(extra="ignore")


class AdaptiveAcuityVoiceStepResponse(BaseModel):
    """Outcome of an interactive voice-controlled optotype submission."""

    test_id: uuid.UUID
    attempt_sequence: int
    test_status: str
    was_correct: bool | None = None
    level: int
    total_attempts: int
    correct_attempts: int
    is_test_complete: bool
    input_modality: str = "VOICE"
    recognition_status: str
    raw_transcript: str
    recognized_symbol: str | None = None
    transcription_confidence: float | None = None
    stt_provider: str | None = None
    retry_required: bool
    feedback_message: str
    next_challenge: OptotypeChallengeResponse | None = None
    result_summary: AdaptiveAcuityResultResponse | None = None

    model_config = ConfigDict(from_attributes=True)
