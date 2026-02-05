"""Security module for the Prompt RAG Agent."""

from .injection_detector import (
    detect_injection,
    detect_all_injections,
    sanitize_for_context,
    get_injection_severity_score,
    InjectionDetection,
    InjectionSeverity
)
from .secret_redactor import (
    redact_secrets,
    redact_secrets_detailed,
    contains_secrets,
    mask_secret,
    RedactionResult
)
from .input_validator import (
    validate_user_request,
    validate_constraints,
    validate_context,
    sanitize_text,
    is_safe_url,
    ValidationResult
)
from .middleware import (
    RequestIdMiddleware,
    SafeLoggingMiddleware,
    APIKeyMiddleware,
    get_request_id
)

__all__ = [
    # Injection detection
    "detect_injection",
    "detect_all_injections", 
    "sanitize_for_context",
    "get_injection_severity_score",
    "InjectionDetection",
    "InjectionSeverity",
    # Secret redaction
    "redact_secrets",
    "redact_secrets_detailed",
    "contains_secrets",
    "mask_secret",
    "RedactionResult",
    # Input validation
    "validate_user_request",
    "validate_constraints",
    "validate_context",
    "sanitize_text",
    "is_safe_url",
    "ValidationResult",
    # Middleware
    "RequestIdMiddleware",
    "SafeLoggingMiddleware",
    "APIKeyMiddleware",
    "get_request_id",
]
