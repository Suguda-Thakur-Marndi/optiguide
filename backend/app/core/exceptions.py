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


class AuthenticationException(OptiGuideException):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(message=message, code="UNAUTHORIZED")


class ForbiddenException(OptiGuideException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(message=message, code="FORBIDDEN")


class TokenExpiredException(AuthenticationException):
    def __init__(self, message: str = "Token has expired."):
        super().__init__(message=message)
        self.code = "TOKEN_EXPIRED"


class TokenInvalidException(AuthenticationException):
    def __init__(self, message: str = "Token is invalid or malformed."):
        super().__init__(message=message)
        self.code = "TOKEN_INVALID"


class TokenRevokedException(AuthenticationException):
    def __init__(self, message: str = "Token has been revoked."):
        super().__init__(message=message)
        self.code = "TOKEN_REVOKED"


class UserAlreadyExistsException(OptiGuideException):
    def __init__(self, message: str = "A user with this email address already exists."):
        super().__init__(message=message, code="CONFLICT")


class UserInactiveException(AuthenticationException):
    def __init__(self, message: str = "User account has been deactivated."):
        super().__init__(message=message)
        self.code = "USER_INACTIVE"


class RateLimitExceededException(OptiGuideException):
    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED")


class ConsentRequiredException(OptiGuideException):
    def __init__(
        self,
        message: str = "Active consent is required to start a preliminary vision screening session.",
    ):
        super().__init__(message=message, code="CONSENT_REQUIRED")


class InvalidConsentVersionException(OptiGuideException):
    def __init__(self, message: str = "Requested consent version is not valid or supported."):
        super().__init__(message=message, code="INVALID_CONSENT_VERSION")


class SessionAlreadyActiveException(OptiGuideException):
    def __init__(
        self,
        message: str = "An active screening session is already in progress. Please complete or cancel it before starting a new one.",
    ):
        super().__init__(message=message, code="SESSION_ALREADY_ACTIVE")


class InvalidSessionTransitionException(OptiGuideException):
    def __init__(self, message: str = "Invalid screening session status transition."):
        super().__init__(message=message, code="INVALID_SESSION_TRANSITION")
