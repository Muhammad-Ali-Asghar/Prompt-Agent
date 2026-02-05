# Secret Handling Guidelines

## Guideline: Secure Secret Management

**ID**: guideline_secret_handling_001
**Category**: Secrets Management
**Severity**: High
**References**: OWASP A02:2021, CWE-798, CWE-259

### Description
Guidelines for securely handling secrets including API keys, passwords, tokens, and other sensitive credentials throughout the application lifecycle.

---

## Core Principles

### Never Hardcode Secrets
Secrets must never appear in:
- Source code
- Configuration files committed to version control
- Log files or error messages
- API responses
- Client-side code

### Use Environment Variables or Secret Managers
```python
# ✓ GOOD: Environment variable
import os
api_key = os.environ.get("API_KEY")

# ✓ GOOD: Secret manager
from cloud_secrets import get_secret
api_key = get_secret("api-key-name")
```

```python
# ✗ BAD: Hardcoded secret
api_key = "sk-12345abcdef67890"
```

---

## Secret Storage

### Development
- Use `.env` files (never commit to git)
- Add `.env` to `.gitignore`
- Provide `.env.example` with placeholder values

### Production
- Use dedicated secret managers:
  - AWS Secrets Manager
  - Google Secret Manager
  - HashiCorp Vault
  - Azure Key Vault
- Rotate secrets regularly
- Implement access logging

### Access Control
- Apply least privilege principle
- Use service accounts with limited scopes
- Audit secret access regularly
- Implement secret versioning

---

## Secret Detection

### Patterns to Detect
| Pattern | Example |
|---------|---------|
| API Key | `api_key=abc123...` |
| AWS Key | `AKIA...` |
| Private Key | `-----BEGIN PRIVATE KEY-----` |
| JWT | `eyJ...` |
| Password | `password=...` |
| Connection String | `postgres://user:pass@host` |

### Pre-commit Checks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

---

## Logging and Monitoring

### Safe Logging
```python
# ✓ GOOD: Redact secrets
logger.info(f"API call to {endpoint} with key {mask(api_key)}")

# ✓ GOOD: Don't log secrets at all
logger.info(f"API call to {endpoint}")
```

```python
# ✗ BAD: Logging secrets
logger.debug(f"Using API key: {api_key}")
```

### Masking Functions
```python
def mask(secret: str, visible: int = 4) -> str:
    """Mask a secret, showing only first few characters."""
    if len(secret) <= visible:
        return "*" * len(secret)
    return secret[:visible] + "*" * (len(secret) - visible)
```

---

## API Response Security

### Never Return Secrets
```python
# ✓ GOOD: Filter sensitive fields
return {
    "user_id": user.id,
    "email": user.email,
    # password_hash NOT included
}

# ✓ GOOD: Use serializers with explicit fields
class UserResponse(BaseModel):
    id: str
    email: str
    # No password field defined
```

### Redact in Error Handling
```python
try:
    connect(connection_string)
except Exception as e:
    # Redact connection string from error
    safe_error = redact_secrets(str(e))
    logger.error(f"Connection failed: {safe_error}")
    raise APIError("Database connection failed")
```

---

## Secret Rotation

### Implement Rotation Strategy
1. Generate new secret
2. Update secret in secret manager
3. Deploy new secret to services
4. Verify new secret works
5. Revoke old secret
6. Monitor for issues

### Design for Rotation
- Support multiple valid secrets during rotation
- Implement graceful fallback
- Log secret version usage
- Alert on old secret usage after rotation
