"""Core custom application exceptions."""

from typing import Any


class OptiGuideException(Exception):
    """Base exception for all OptiGuide application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        details: list[Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or []


class EntityNotFoundException(OptiGuideException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            code="NOT_FOUND",
        )


class ValidationException(OptiGuideException):
    def __init__(self, message: str, details: list[Any] | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class DatabaseConnectionException(OptiGuideException):
    def __init__(self, message: str = "Unable to connect to database."):
        super().__init__(message=message, code="DATABASE_DISCONNECTED")
