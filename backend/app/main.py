import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure backend root is on sys.path for both 'app' and 'backend.app' executions
_backend_root = str(Path(__file__).resolve().parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import OptiGuideException
from app.core.logging import logger
from app.middleware.error_handler import (
    generic_exception_handler,
    http_exception_handler,
    optiguide_exception_handler,
    validation_exception_handler,
)
from app.middleware.logging_middleware import RequestTimingMiddleware
from app.schemas.health import AppInfoResponse, HealthResponse


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="OptiGuide Vision Screening and Eyewear Guidance API",
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
    )

    # Middleware: Request timing
    app.add_middleware(RequestTimingMiddleware)

    # Middleware: CORS
    cors_kwargs = {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if settings.APP_ENV != "production":
        cors_kwargs["allow_origin_regex"] = r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"
    app.add_middleware(CORSMiddleware, **cors_kwargs)

    # Exception Handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(OptiGuideException, optiguide_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Root Identification Endpoint
    @app.get("/", response_model=AppInfoResponse, tags=["General"])
    async def root_info() -> AppInfoResponse:
        return AppInfoResponse(
            name=f"{settings.APP_NAME} API",
            version=settings.APP_VERSION,
            status="running",
            environment=settings.APP_ENV,
        )

    # Root Level Health (Liveness)
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def root_health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=f"{settings.APP_NAME.lower()}-api",
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
            timestamp=datetime.now(UTC).isoformat(),
        )

    # Interactive Voice Tester Web UI
    @app.get("/voice-test", response_class=HTMLResponse, tags=["Voice Assistant"])
    async def voice_test_ui():
        root_path = Path(__file__).resolve().parent.parent.parent
        html_file = root_path / "voice_tester.html"
        if not html_file.exists():
            html_file = root_path / "backend" / "voice_tester.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
        return HTMLResponse(
            content="<h1>OptiGuide Voice Assistant</h1><p>voice_tester.html is available in project root.</p>"
        )

    # Include API v1 Router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    logger.info(f"{settings.APP_NAME} initialized in {settings.APP_ENV} environment.")
    return app


app = create_application()
