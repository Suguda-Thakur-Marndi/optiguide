from pydantic import BaseModel, Field


class AppInfoResponse(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "OptiGuide API"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    status: str = Field(..., json_schema_extra={"example": "running"})
    environment: str = Field(..., json_schema_extra={"example": "development"})


class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ok"})
    service: str = Field(..., json_schema_extra={"example": "optiguide-api"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    environment: str | None = Field(None, json_schema_extra={"example": "development"})
    timestamp: str | None = Field(None, json_schema_extra={"example": "2026-11-03T01:00:00.000Z"})
    database: str | None = Field(None, json_schema_extra={"example": "connected"})


class DatabaseHealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ok"})
    database: str = Field(..., json_schema_extra={"example": "connected"})
    database_type: str | None = Field(None, json_schema_extra={"example": "sqlite"})
    latency_ms: float | None = Field(None, json_schema_extra={"example": 1.23})
    message: str | None = Field(None, json_schema_extra={"example": "Database ping successful"})
