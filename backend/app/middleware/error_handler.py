from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import OptiGuideException
from app.core.logging import logger


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats 422 validation errors into standard error envelope."""
    details = []
    for err in exc.errors():
        details.append(
            {
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
        )

    payload = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "The request payload failed validation.",
            "details": details,
        }
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Formats HTTP exceptions (404, 400, etc.) into standard error envelope."""
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, "ERROR")

    # If detail is already a dict with error structure, preserve it
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    payload = {
        "error": {
            "code": code,
            "message": str(exc.detail) if exc.detail else "An HTTP error occurred.",
            "details": [],
        }
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


async def optiguide_exception_handler(request: Request, exc: OptiGuideException):
    """Formats domain OptiGuideExceptions into standard error envelope with mapped status code."""
    status_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "TOKEN_EXPIRED": status.HTTP_401_UNAUTHORIZED,
        "TOKEN_INVALID": status.HTTP_401_UNAUTHORIZED,
        "TOKEN_REVOKED": status.HTTP_401_UNAUTHORIZED,
        "USER_INACTIVE": status.HTTP_403_FORBIDDEN,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "CONSENT_REQUIRED": status.HTTP_403_FORBIDDEN,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "SESSION_ALREADY_ACTIVE": status.HTTP_409_CONFLICT,
        "INVALID_CONSENT_VERSION": status.HTTP_400_BAD_REQUEST,
        "INVALID_SESSION_TRANSITION": status.HTTP_400_BAD_REQUEST,
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "DATABASE_DISCONNECTED": status.HTTP_503_SERVICE_UNAVAILABLE,
        "INTERNAL_SERVER_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    http_status = status_map.get(exc.code, status.HTTP_400_BAD_REQUEST)
    payload = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        }
    }
    return JSONResponse(status_code=http_status, content=payload)


async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled exceptions, logs traceback, and returns safe 500 error."""
    logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {exc}")
    payload = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred. Please try again later.",
            "details": [],
        }
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
