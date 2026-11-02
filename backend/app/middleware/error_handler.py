from backend.app.core.logging import logger
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


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
