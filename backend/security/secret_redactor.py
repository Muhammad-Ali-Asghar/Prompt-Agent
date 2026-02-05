"""
Secret redaction utilities for the Prompt RAG Agent.
Detects and redacts sensitive information from text.
"""

import re
from typing import NamedTuple


class RedactionResult(NamedTuple):
    """Result of redaction with metadata."""
    text: str
    redacted_count: int
    redaction_types: list[str]


# Patterns for detecting secrets
SECRET_PATTERNS = [
    # Generic API keys
    (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', "API_KEY"),
    (r'(?i)(secret|token|password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', "SECRET"),
    
    # Bearer tokens
    (r'(?i)bearer\s+([a-zA-Z0-9_\-\.]+)', "BEARER_TOKEN"),
    
    # AWS credentials
    (r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[:=]\s*["\']?([A-Z0-9]{20})["\']?', "AWS_ACCESS_KEY"),
    (r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?', "AWS_SECRET_KEY"),
    (r'AKIA[0-9A-Z]{16}', "AWS_KEY_ID"),
    
    # Google Cloud
    (r'(?i)(google[_-]?api[_-]?key|gcp[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{35,})["\']?', "GCP_KEY"),
    (r'AIza[0-9A-Za-z_\-]{35}', "GOOGLE_API_KEY"),
    
    # Azure
    (r'(?i)(azure[_-]?key|azure[_-]?secret)\s*[:=]\s*["\']?([a-zA-Z0-9+/=]{40,})["\']?', "AZURE_KEY"),
    
    # Private keys
    (r'-----BEGIN (?:RSA |OPENSSH |DSA |EC )?PRIVATE KEY-----', "PRIVATE_KEY"),
    
    # GitHub tokens
    (r'gh[pousr]_[A-Za-z0-9_]{36,}', "GITHUB_TOKEN"),
    (r'github_pat_[A-Za-z0-9_]{22,}', "GITHUB_PAT"),
    
    # Slack tokens
    (r'xox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{20,}', "SLACK_TOKEN"),
    
    # JWT tokens (detect the structure)
    (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', "JWT_TOKEN"),
    
    # Generic hex tokens (32+ chars)
    (r'(?<![a-fA-F0-9])[a-fA-F0-9]{32,}(?![a-fA-F0-9])', "HEX_TOKEN"),
    
    # Environment variable references that might contain secrets
    (r'\$\{?(?:API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIALS)[A-Z_]*\}?', "ENV_VAR_REF"),
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [(re.compile(pattern), name) for pattern, name in SECRET_PATTERNS]


def redact_secrets(text: str, replacement: str = "[REDACTED]") -> str:
    """
    Redact secrets from text.
    
    Args:
        text: Input text to scan and redact
        replacement: String to replace secrets with
    
    Returns:
        Text with secrets redacted
    """
    if not text:
        return text
    
    result = text
    for pattern, _ in COMPILED_PATTERNS:
        result = pattern.sub(replacement, result)
    
    return result


def redact_secrets_detailed(text: str, replacement: str = "[REDACTED]") -> RedactionResult:
    """
    Redact secrets with detailed information about what was found.
    
    Args:
        text: Input text to scan and redact
        replacement: String to replace secrets with
    
    Returns:
        RedactionResult with redacted text and metadata
    """
    if not text:
        return RedactionResult(text, 0, [])
    
    result = text
    redacted_count = 0
    redaction_types = []
    
    for pattern, secret_type in COMPILED_PATTERNS:
        matches = pattern.findall(result)
        if matches:
            count = len(matches) if isinstance(matches[0], str) else len(matches)
            redacted_count += count
            if secret_type not in redaction_types:
                redaction_types.append(secret_type)
            result = pattern.sub(replacement, result)
    
    return RedactionResult(result, redacted_count, redaction_types)


def contains_secrets(text: str) -> bool:
    """
    Check if text contains any detectable secrets.
    
    Args:
        text: Input text to scan
    
    Returns:
        True if secrets detected, False otherwise
    """
    if not text:
        return False
    
    for pattern, _ in COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    
    return False


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """
    Partially mask a secret, showing only first few characters.
    
    Args:
        secret: The secret to mask
        visible_chars: Number of characters to keep visible
    
    Returns:
        Masked secret like "sk-a****"
    """
    if len(secret) <= visible_chars:
        return "*" * len(secret)
    
    return secret[:visible_chars] + "*" * (len(secret) - visible_chars)
