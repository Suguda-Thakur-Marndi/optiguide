import uuid
from datetime import datetime
from enum import Enum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field


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
    """
    Payload for accepting the server-controlled screening consent.
    Reconciles 'version' and 'consent_version' naming discrepancies.
    """

    version: str = Field(
        ...,
        validation_alias=AliasChoices("version", "consent_version"),
        max_length=50,
        json_schema_extra={"example": "1.0.0"},
    )

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ConsentResponse(BaseModel):
    """
    Model representation of a recorded consent decision.
    Exposes canonical 'consent_version' and 'consent_text_hash',
    plus backward-compatible computed aliases 'version' and 'hash'.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    consent_version: str
    consent_text_hash: str
    accepted_at: datetime
    withdrawn_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    def version(self) -> str:
        return self.consent_version

    @computed_field
    def hash(self) -> str:
        return self.consent_text_hash

    model_config = ConfigDict(from_attributes=True)


class ScreeningSessionCreateRequest(BaseModel):
    """
    Payload for initiating a screening session.
    Strictly empty schema that forbids any client-injected fields, IDs, or statuses.
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
    notes: str | None = None
    device_info: str | None = None
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
