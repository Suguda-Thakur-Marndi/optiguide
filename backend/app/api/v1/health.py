from datetime import UTC, datetime

from backend.app.core.config import settings
from backend.app.database.session import check_db_connectivity
from backend.app.schemas.health import DatabaseHealthResponse, HealthResponse
from fastapi import APIRouter, Response, status

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health Check",
    description="Returns operational status of OptiGuide API and database connection.",
)
async def get_system_health(response: Response) -> HealthResponse:
    is_connected, _, _, _ = check_db_connectivity()
    now_utc = datetime.now(UTC).isoformat()

    if is_connected:
        return HealthResponse(
            status="ok",
            service=f"{settings.APP_NAME.lower()}-api",
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
            timestamp=now_utc,
            database="connected",
        )
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="degraded",
            service=f"{settings.APP_NAME.lower()}-api",
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
            timestamp=now_utc,
            database="disconnected",
        )


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    summary="Database Connectivity Health Check",
    description="Performs live connection check against the configured database.",
)
@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    include_in_schema=False,
    summary="Database Connectivity Diagnostic Alias",
)
async def get_db_health(response: Response) -> DatabaseHealthResponse:
    is_connected, latency_ms, db_type, error_msg = check_db_connectivity()

    if is_connected:
        return DatabaseHealthResponse(
            status="ok",
            database="connected",
            database_type=db_type,
            latency_ms=latency_ms,
            message="Database ping successful",
        )
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DatabaseHealthResponse(
            status="error",
            database="disconnected",
            database_type=db_type,
            latency_ms=None,
            message=error_msg or "Database connection failed",
        )
