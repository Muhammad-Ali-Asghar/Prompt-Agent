"""
Security middleware for the Prompt RAG Agent.
Includes request ID injection, API key authentication, and safe logging.
"""

import uuid
import time
import logging
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config import get_settings
from security.secret_redactor import redact_secrets

# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="no-request-id")

logger = logging.getLogger(__name__)


class RequestIdFilter(logging.Filter):
    """Logging filter that adds request_id to log records."""

    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


# Filter logic will be attached in main.py lifespan


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to inject unique request ID into each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        # Store in request state for access in endpoints
        request.state.request_id = request_id

        # Process request and add ID to response
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class SafeLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for safe structured logging without sensitive data."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        request_id = getattr(request.state, "request_id", "unknown")

        start_time = time.time()

        # Log request (sanitized)
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "client_ip": self._get_client_ip(request),
        }

        # Only log body in debug mode and with opt-in
        if settings.debug and settings.log_user_requests:
            log_data["query_params"] = str(request.query_params)

        logger.info(f"Request started: {log_data}")

        try:
            response = await call_next(request)

            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Request completed: status={response.status_code} "
                f"duration={process_time:.3f}s"
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time
            # Redact any secrets from error message
            safe_error = redact_secrets(str(e))
            logger.error(
                f"Request failed: error={safe_error} duration={process_time:.3f}s"
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key authentication."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()

        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check API key
        api_key = request.headers.get(settings.api_key_header)

        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Missing API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if api_key not in settings.valid_api_keys:
            logger.warning(f"Invalid API key attempt from {request.client.host}")
            raise HTTPException(status_code=403, detail="Invalid API key")

        return await call_next(request)


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()
