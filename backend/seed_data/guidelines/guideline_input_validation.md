# Input Validation Guidelines

## Guideline: Comprehensive Input Validation

**ID**: guideline_input_validation_001
**Category**: Input Validation
**Severity**: High
**References**: OWASP A03:2021, CWE-20, CWE-1284

### Description
Guidelines for validating and sanitizing all external input to prevent injection attacks, data corruption, and application errors.

---

## Core Principles

### Validate All External Input
External input sources include:
- HTTP request parameters (query, body, headers)
- File uploads
- Database results (consider as untrusted)
- Third-party API responses
- Environment variables (at startup)
- Command line arguments

### Defense in Depth
1. Client-side validation (UX only, never trust)
2. API gateway validation (rate limiting, size limits)
3. Application layer validation (business rules)
4. Database layer validation (constraints, types)

---

## Validation Strategies

### Allowlist (Preferred)
```python
# ✓ GOOD: Allowlist of valid values
VALID_STATUSES = {"pending", "approved", "rejected"}
if status not in VALID_STATUSES:
    raise ValidationError("Invalid status")

# ✓ GOOD: Regex for format validation
import re
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
if not EMAIL_PATTERN.match(email):
    raise ValidationError("Invalid email format")
```

### Type Validation
```python
# ✓ GOOD: Strong typing with Pydantic
from pydantic import BaseModel, Field, validator

class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    age: int = Field(..., ge=0, le=150)
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower()
```

### Size Limits
```python
# ✓ GOOD: Enforce size limits
MAX_REQUEST_SIZE = 10 * 1024  # 10KB

if len(request.body) > MAX_REQUEST_SIZE:
    raise ValidationError("Request too large")

# ✓ GOOD: Limit array lengths
if len(items) > 100:
    raise ValidationError("Too many items")
```

---

## Common Validation Rules

### Strings
| Validation | Purpose |
|------------|---------|
| Max length | Prevent buffer issues |
| Min length | Ensure meaningful input |
| Pattern match | Enforce format |
| Character set | Block dangerous chars |
| Encoding | Normalize to UTF-8 |

### Numbers
| Validation | Purpose |
|------------|---------|
| Type check | Ensure numeric |
| Range (min/max) | Business constraints |
| Precision | Decimal places |
| Sign | Positive/negative |

### Files
| Validation | Purpose |
|------------|---------|
| Size limit | Prevent DoS |
| Type (magic bytes) | True file type |
| Extension | Basic filter |
| Filename | Path traversal |
| Content scan | Malware |

---

## Sanitization

### String Sanitization
```python
import unicodedata
import re

def sanitize_text(text: str) -> str:
    # Normalize Unicode
    text = unicodedata.normalize('NFC', text)
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text
```

### Path Sanitization
```python
import os

def safe_join(base: str, user_path: str) -> str:
    """Safely join paths preventing traversal."""
    # Normalize and resolve
    base = os.path.abspath(base)
    full_path = os.path.abspath(os.path.join(base, user_path))
    
    # Ensure result is under base
    if not full_path.startswith(base):
        raise SecurityError("Path traversal detected")
    
    return full_path
```

---

## Error Handling

### Safe Error Messages
```python
# ✓ GOOD: Generic error to client
try:
    validate_input(data)
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    return {"error": "Invalid input"}, 400

# ✗ BAD: Detailed error to client
try:
    validate_input(data)
except ValidationError as e:
    return {"error": str(e)}, 400  # May leak info
```

### Fail Closed
```python
# ✓ GOOD: Fail closed on validation error
try:
    validated_data = validate(raw_data)
except Exception:
    logger.error("Validation failed unexpectedly")
    raise HTTPException(400, "Invalid request")
    # Never proceed with unvalidated data
```
