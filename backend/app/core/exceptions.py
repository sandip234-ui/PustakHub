"""
Application-level exception definitions and global exception handlers.

Establishes a predictable JSON error response shape for all API errors.
Future phases will extend these handlers as new error categories emerge.

All error responses conform to the following shape:
    {
        "error": "<machine-readable error code>",
        "message": "<human-readable description>",
        "detail": <optional extra context, or null>
    }
"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Error response schema
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standard error payload returned by all error handlers."""

    error: str
    message: str
    detail: object = None


# ---------------------------------------------------------------------------
# Custom application exceptions
# ---------------------------------------------------------------------------


class PustakHubError(Exception):
    """Base exception for all domain-level PustakHub errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, detail: object = None) -> None:
        self.message = message or self.__class__.message
        self.detail = detail
        super().__init__(self.message)


class NotFoundError(PustakHubError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    message = "The requested resource was not found."


class ValidationError(PustakHubError):
    """Raised when business-level validation fails (not Pydantic schema validation)."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "validation_error"
    message = "The provided data is invalid."


class ConflictError(PustakHubError):
    """Raised when a resource conflict occurs (e.g., duplicate entry)."""

    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"
    message = "A conflict occurred with existing data."


class ForbiddenError(PustakHubError):
    """Raised when an action is not permitted for the caller."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"
    message = "You do not have permission to perform this action."


class RateLimitExceededError(PustakHubError):
    """Raised when request rate limit is exceeded (HTTP 429)."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "rate_limit_exceeded"
    message = "Too many requests. Please try again later."


class PayloadTooLargeError(PustakHubError):
    """Raised when request payload exceeds allowed limit (HTTP 413)."""

    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    error_code = "payload_too_large"
    message = "Request payload exceeds the maximum permitted size."


class ServiceUnavailableError(PustakHubError):
    """Raised when a required backend service (e.g., Redis for auth) is unavailable (HTTP 503)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "service_unavailable"
    message = "Service temporarily unavailable. Please try again later."


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


def _error_json(
    status_code: int,
    error_code: str,
    message: str,
    detail: object = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=error_code,
            message=message,
            detail=detail,
        ).model_dump(),
    )


async def pustak_hub_exception_handler(
    request: Request, exc: PustakHubError
) -> JSONResponse:
    """Handle all domain-level PustakHub exceptions."""
    return _error_json(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        detail=getattr(exc, "detail", None),
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic request validation errors with a consistent shape."""
    return _error_json(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error_code="request_validation_error",
        message="Request body or parameters failed validation.",
        detail=jsonable_encoder(exc.errors()),
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler for unexpected server errors."""
    # NOTE: Do not expose internal exception details to the client in production.
    return _error_json(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="internal_server_error",
        message="An unexpected internal error occurred.",
    )


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers on the FastAPI application.

    Call this once in main.py during application setup.
    """
    app.add_exception_handler(PustakHubError, pustak_hub_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
