"""
Request Body Size Protection Middleware for PustakHub.

Guards endpoints against oversized payload denial-of-service (DoS) attacks
by validating Content-Length and limiting incoming payload size.
"""

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that rejects requests with body size exceeding settings.MAX_REQUEST_BODY_SIZE.
    Protects against both Content-Length-specified payloads and streamed/chunked payloads.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        max_size = settings.MAX_REQUEST_BODY_SIZE
        content_length = request.headers.get("content-length")

        # 1. Fast path: check explicit Content-Length header
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > max_size:
                    logger.warning(
                        "Rejected oversized request (%d bytes > %d limit) from %s on %s %s",
                        length_int,
                        max_size,
                        request.client.host if request.client else "unknown",
                        request.method,
                        request.url.path,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "payload_too_large",
                            "message": f"Request payload exceeds the maximum permitted size of {max_size} bytes.",
                            "detail": None,
                        },
                    )
            except ValueError:
                pass  # Ignore invalid non-integer content-length and let downstream handle

        # 2. Streaming / chunked transfer incremental byte counting
        total_received = 0
        original_receive = request.receive

        request.state.payload_too_large = False

        async def limited_receive():
            nonlocal total_received
            message = await original_receive()
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                total_received += len(chunk)
                if total_received > max_size:
                    request.state.payload_too_large = True
                    logger.warning(
                        "Rejected streaming request exceeding limit (%d bytes > %d limit) from %s on %s %s",
                        total_received,
                        max_size,
                        request.client.host if request.client else "unknown",
                        request.method,
                        request.url.path,
                    )
                    from app.core.exceptions import PayloadTooLargeError
                    raise PayloadTooLargeError(
                        message=f"Request payload exceeds the maximum permitted size of {max_size} bytes."
                    )
            return message

        request._receive = limited_receive

        try:
            response = await call_next(request)
            if getattr(request.state, "payload_too_large", False):
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "payload_too_large",
                        "message": f"Request payload exceeds the maximum permitted size of {max_size} bytes.",
                        "detail": None,
                    },
                )
            return response
        except Exception as exc:
            from app.core.exceptions import PayloadTooLargeError
            if getattr(request.state, "payload_too_large", False) or isinstance(exc, PayloadTooLargeError):
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "payload_too_large",
                        "message": f"Request payload exceeds the maximum permitted size of {max_size} bytes.",
                        "detail": None,
                    },
                )
            raise
