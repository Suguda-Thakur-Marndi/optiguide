import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ScreeningSessionStatus(str, Enum):
    """Controlled lifecycle statuses for preliminary vision screening sessions."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConsentStatusResponse(BaseModel):
    """Represents the current server-controlled consent document and user state."""

    version: str
    title: str
    content: str
    hash: str
    has_accepted: bool
    is_active: bool
    accepted_at: datetime | None = None
    withdrawn_at: datetime | None = None


class ConsentAcceptRequest(BaseModel):
    """Payload for accepting the server-controlled screening consent."""

    version: str = Field(..., max_length=50, json_schema_extra={"example": "1.0.0"})

    model_config = ConfigDict(extra="forbid")


class ConsentResponse(BaseModel):
    """Model representation of a recorded consent decision."""

    id: uuid.UUID
    user_id: uuid.UUID
    consent_version: str
    consent_text_hash: str
    accepted_at: datetime
    withdrawn_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreeningSessionCreateRequest(BaseModel):
    """
    Payload for initiating a screening session.
    Strictly forbids client-injected status, IDs, or timestamps.
    """

    model_config = ConfigDict(extra="forbid")


class ScreeningSessionCancelRequest(BaseModel):
    """Optional payload when cancelling an in-progress screening session."""

    reason: str | None = Field(
        default=None,
        max_length=255,
        json_schema_extra={"example": "User paused test to consult eye care professional."},
    )

    model_config = ConfigDict(extra="forbid")


class ScreeningSessionResponse(BaseModel):
    """Public representation of a screening session record."""

    id: uuid.UUID
    user_id: uuid.UUID
    consent_id: uuid.UUID
    status: str
    cancellation_reason: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreeningSessionListResponse(BaseModel):
    """Paginated list of screening sessions belonging to the authenticated user."""

    items: list[ScreeningSessionResponse]
    total: int
    limit: int
    offset: int
