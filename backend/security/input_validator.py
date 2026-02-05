"""
Input validation and sanitization for the Prompt RAG Agent.
Enforces size limits and cleans potentially dangerous input.
"""

import re
import unicodedata
from typing import NamedTuple

from config import get_settings


class ValidationResult(NamedTuple):
    """Result of input validation."""
    is_valid: bool
    sanitized_text: str
    errors: list[str]
    warnings: list[str]


# Dangerous control characters to remove
CONTROL_CHARS = (
    '\x00\x01\x02\x03\x04\x05\x06\x07\x08'  # NUL through BS
    '\x0b\x0c'  # VT and FF
    '\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'  # SO through US
    '\x7f'  # DEL
)

# Pattern for control characters
CONTROL_CHAR_PATTERN = re.compile(f'[{re.escape(CONTROL_CHARS)}]')

# Pattern for excessive whitespace
EXCESSIVE_WHITESPACE_PATTERN = re.compile(r'[ \t]{10,}')
EXCESSIVE_NEWLINES_PATTERN = re.compile(r'\n{5,}')

# Pattern for null bytes and other binary garbage
BINARY_GARBAGE_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]+')


def validate_user_request(text: str) -> ValidationResult:
    """
    Validate and sanitize user request input.
    
    Args:
        text: Raw user input
    
    Returns:
        ValidationResult with sanitized text and any errors/warnings
    """
    settings = get_settings()
    errors = []
    warnings = []
    
    if not text:
        return ValidationResult(False, "", ["User request cannot be empty"], [])
    
    # Check size limit
    if len(text.encode('utf-8')) > settings.max_request_size:
        errors.append(
            f"Request exceeds maximum size of {settings.max_request_size} bytes"
        )
        return ValidationResult(False, "", errors, [])
    
    # Sanitize
    sanitized = sanitize_text(text)
    
    # Check if significant content was removed
    if len(sanitized) < len(text) * 0.5:
        warnings.append("Significant portion of input was removed during sanitization")
    
    # Warn about very short requests
    if len(sanitized.strip()) < 10:
        warnings.append("Request is very short, may produce generic results")
    
    return ValidationResult(True, sanitized, errors, warnings)


def validate_constraints(constraints: list[str]) -> ValidationResult:
    """
    Validate and sanitize constraint strings.
    
    Args:
        constraints: List of constraint strings
    
    Returns:
        ValidationResult with sanitized constraints joined
    """
    errors = []
    warnings = []
    sanitized_constraints = []
    
    if not constraints:
        return ValidationResult(True, "", [], [])
    
    if len(constraints) > 20:
        warnings.append("Large number of constraints may reduce prompt quality")
    
    for i, constraint in enumerate(constraints):
        if not isinstance(constraint, str):
            warnings.append(f"Constraint {i} is not a string, skipping")
            continue
        
        if len(constraint) > 500:
            warnings.append(f"Constraint {i} is very long, truncating")
            constraint = constraint[:500]
        
        sanitized = sanitize_text(constraint)
        if sanitized.strip():
            sanitized_constraints.append(sanitized.strip())
    
    return ValidationResult(
        True, 
        "\n".join(sanitized_constraints), 
        errors, 
        warnings
    )


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing dangerous characters and normalizing.
    
    Args:
        text: Raw text input
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    result = text
    
    # Normalize Unicode (NFC form)
    result = unicodedata.normalize('NFC', result)
    
    # Remove control characters (keep tab, newline, carriage return)
    result = CONTROL_CHAR_PATTERN.sub('', result)
    
    # Remove binary garbage
    result = BINARY_GARBAGE_PATTERN.sub('', result)
    
    # Normalize excessive whitespace
    result = EXCESSIVE_WHITESPACE_PATTERN.sub('    ', result)
    result = EXCESSIVE_NEWLINES_PATTERN.sub('\n\n\n', result)
    
    # Remove null bytes specifically (safety)
    result = result.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    result = result.strip()
    
    return result


def validate_context(context: str | None) -> ValidationResult:
    """
    Validate optional context string.
    
    Args:
        context: Optional context/project details
    
    Returns:
        ValidationResult with sanitized context
    """
    if not context:
        return ValidationResult(True, "", [], [])
    
    warnings = []
    
    # Context can be larger than user_request
    max_context_size = 50000  # 50KB
    
    if len(context.encode('utf-8')) > max_context_size:
        warnings.append(f"Context truncated to {max_context_size} bytes")
        # Truncate by characters (approximate)
        context = context[:max_context_size]
    
    sanitized = sanitize_text(context)
    
    return ValidationResult(True, sanitized, [], warnings)


def is_safe_url(url: str) -> bool:
    """
    Check if a URL is safe (not targeting internal resources).
    Blocks private IP ranges and local file paths.
    
    Args:
        url: URL to check
    
    Returns:
        True if URL is safe, False otherwise
    """
    import urllib.parse
    
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False
    
    # Block file:// protocol
    if parsed.scheme == 'file':
        return False
    
    # Block non-http(s) protocols
    if parsed.scheme not in ('http', 'https'):
        return False
    
    hostname = parsed.hostname
    if not hostname:
        return False
    
    hostname_lower = hostname.lower()
    
    # Block localhost
    if hostname_lower in ('localhost', '127.0.0.1', '::1'):
        return False
    
    # Block private IP ranges
    private_patterns = [
        r'^10\.',  # 10.0.0.0/8
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # 172.16.0.0/12
        r'^192\.168\.',  # 192.168.0.0/16
        r'^169\.254\.',  # Link-local
        r'^0\.',  # 0.0.0.0/8
    ]
    
    for pattern in private_patterns:
        if re.match(pattern, hostname):
            return False
    
    # Block internal hostnames
    internal_patterns = ['internal', 'intranet', 'corp', 'private', 'local']
    for pattern in internal_patterns:
        if pattern in hostname_lower:
            return False
    
    return True
