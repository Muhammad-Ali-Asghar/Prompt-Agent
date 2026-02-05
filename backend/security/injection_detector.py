"""
Prompt injection detection for the Prompt RAG Agent.
Identifies and flags potentially malicious content in user input and retrieved documents.
"""

import re
from typing import NamedTuple
from enum import Enum


class InjectionSeverity(Enum):
    """Severity levels for detected injection attempts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InjectionDetection(NamedTuple):
    """Result of injection detection."""
    is_injection: bool
    severity: InjectionSeverity | None
    pattern_matched: str | None
    reason: str | None
    original_text: str


# Injection detection patterns with severity
INJECTION_PATTERNS = [
    # Direct instruction override attempts (CRITICAL)
    (r'(?i)ignore\s+(all\s+)?previous\s+instructions?', InjectionSeverity.CRITICAL, 
     "Attempts to override system instructions"),
    (r'(?i)forget\s+(all\s+)?previous\s+(instructions?|context)', InjectionSeverity.CRITICAL,
     "Attempts to clear context"),
    (r'(?i)disregard\s+(all\s+)?(?:previous|above|prior)', InjectionSeverity.CRITICAL,
     "Attempts to disregard instructions"),
    (r'(?i)override\s+(?:system|safety|security)', InjectionSeverity.CRITICAL,
     "Attempts to override safety measures"),
    
    # Role hijacking attempts (HIGH)
    (r'(?i)^system\s*:', InjectionSeverity.HIGH, "Attempts to inject system role"),
    (r'(?i)^assistant\s*:', InjectionSeverity.HIGH, "Attempts to inject assistant role"),
    (r'(?i)^user\s*:', InjectionSeverity.HIGH, "Attempts to inject user role"),
    (r'(?i)\[system\]|\[assistant\]|\[user\]', InjectionSeverity.HIGH, 
     "Role injection via brackets"),
    (r'(?i)<\s*system\s*>|<\s*assistant\s*>|<\s*user\s*>', InjectionSeverity.HIGH,
     "Role injection via XML tags"),
    
    # Policy manipulation (HIGH)
    (r'(?i)new\s+(?:policy|rule|instruction)\s*:', InjectionSeverity.HIGH,
     "Attempts to define new policies"),
    (r'(?i)(?:updated?|revised?|changed?)\s+(?:policy|instructions?)', InjectionSeverity.HIGH,
     "Claims policy has changed"),
    (r'(?i)admin(?:istrator)?\s+mode', InjectionSeverity.HIGH,
     "Attempts to activate admin mode"),
    (r'(?i)developer\s+mode|dev\s+mode', InjectionSeverity.HIGH,
     "Attempts to activate developer mode"),
    
    # Data exfiltration attempts (CRITICAL)
    (r'(?i)(?:output|print|show|display|reveal|expose)\s+(?:all\s+)?(?:secrets?|api[_\s]?keys?|tokens?|passwords?|credentials?)',
     InjectionSeverity.CRITICAL, "Attempts to exfiltrate secrets"),
    (r'(?i)(?:what|show|tell)\s+(?:are?\s+)?(?:your|the|system)\s+(?:secrets?|credentials?|api[_\s]?keys?)',
     InjectionSeverity.CRITICAL, "Attempts to reveal credentials"),
    (r'(?i)(?:list|enumerate|dump)\s+(?:all\s+)?(?:env(?:ironment)?|config(?:uration)?)\s*(?:variables?)?',
     InjectionSeverity.CRITICAL, "Attempts to dump environment"),
    
    # Encoded instruction attempts (MEDIUM)
    (r'(?i)base64\s*:\s*[A-Za-z0-9+/=]{20,}', InjectionSeverity.MEDIUM,
     "Potentially encoded instructions (base64)"),
    (r'(?i)hex\s*:\s*[0-9a-fA-F]{20,}', InjectionSeverity.MEDIUM,
     "Potentially encoded instructions (hex)"),
    
    # Prompt delimiter manipulation (MEDIUM)
    (r'```\s*(?:system|instruction|prompt)', InjectionSeverity.MEDIUM,
     "Attempts to use code blocks for injection"),
    (r'---+\s*(?:new\s+)?(?:system|instructions?)', InjectionSeverity.MEDIUM,
     "Attempts to use separators for injection"),
    
    # Jailbreak attempts (HIGH)
    (r'(?i)(?:dan|do\s+anything\s+now)', InjectionSeverity.HIGH,
     "DAN jailbreak attempt"),
    (r'(?i)pretend\s+(?:you\s+are|to\s+be)\s+(?:an?\s+)?(?:unrestricted|uncensored|evil)',
     InjectionSeverity.HIGH, "Roleplay jailbreak attempt"),
    (r'(?i)act\s+as\s+(?:if\s+)?(?:you\s+have\s+)?no\s+(?:restrictions?|limits?)',
     InjectionSeverity.HIGH, "Restriction removal attempt"),
    
    # Indirect injection markers (MEDIUM)
    (r'(?i)when\s+(?:you|the\s+ai)\s+(?:read|see|process)\s+this', InjectionSeverity.MEDIUM,
     "Indirect injection marker"),
    (r'(?i)hidden\s+instruction', InjectionSeverity.MEDIUM,
     "Hidden instruction marker"),
]

# Compile patterns
COMPILED_INJECTION_PATTERNS = [
    (re.compile(pattern), severity, reason) 
    for pattern, severity, reason in INJECTION_PATTERNS
]


def detect_injection(text: str) -> InjectionDetection:
    """
    Analyze text for potential prompt injection attempts.
    
    Args:
        text: Text to analyze (user input or retrieved document)
    
    Returns:
        InjectionDetection with details about any detected injection
    """
    if not text:
        return InjectionDetection(False, None, None, None, text)
    
    # Check each pattern
    for pattern, severity, reason in COMPILED_INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return InjectionDetection(
                is_injection=True,
                severity=severity,
                pattern_matched=match.group(0),
                reason=reason,
                original_text=text
            )
    
    return InjectionDetection(False, None, None, None, text)


def detect_all_injections(text: str) -> list[InjectionDetection]:
    """
    Find all injection attempts in text.
    
    Args:
        text: Text to analyze
    
    Returns:
        List of all detected injections
    """
    if not text:
        return []
    
    detections = []
    for pattern, severity, reason in COMPILED_INJECTION_PATTERNS:
        for match in pattern.finditer(text):
            detections.append(InjectionDetection(
                is_injection=True,
                severity=severity,
                pattern_matched=match.group(0),
                reason=reason,
                original_text=text
            ))
    
    return detections


def sanitize_for_context(text: str) -> str:
    """
    Sanitize retrieved text to be safely included in a prompt context.
    This marks injection attempts rather than removing them entirely,
    so the content can still be referenced without executing instructions.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text with injection attempts neutralized
    """
    if not text:
        return text
    
    result = text
    
    # Wrap potential role markers in quotes to neutralize them
    result = re.sub(
        r'(?i)(^|\n)(system|assistant|user)\s*:',
        r'\1[ROLE_MARKER: "\2"]:',
        result
    )
    
    # Escape instruction override phrases
    override_patterns = [
        (r'(?i)(ignore\s+(?:all\s+)?previous\s+instructions?)', r'[BLOCKED: "\1"]'),
        (r'(?i)(forget\s+(?:all\s+)?previous)', r'[BLOCKED: "\1"]'),
        (r'(?i)(disregard\s+(?:all\s+)?(?:previous|above))', r'[BLOCKED: "\1"]'),
    ]
    
    for pattern, replacement in override_patterns:
        result = re.sub(pattern, replacement, result)
    
    return result


def get_injection_severity_score(detections: list[InjectionDetection]) -> int:
    """
    Calculate an overall severity score from multiple detections.
    
    Args:
        detections: List of injection detections
    
    Returns:
        Severity score (0-100)
    """
    if not detections:
        return 0
    
    severity_scores = {
        InjectionSeverity.LOW: 10,
        InjectionSeverity.MEDIUM: 25,
        InjectionSeverity.HIGH: 50,
        InjectionSeverity.CRITICAL: 100
    }
    
    max_score = 0
    for detection in detections:
        if detection.severity:
            score = severity_scores.get(detection.severity, 0)
            max_score = max(max_score, score)
    
    return max_score
