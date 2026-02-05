"""
Tests for the secret redactor module.
"""

import pytest
from security.secret_redactor import (
    redact_secrets,
    redact_secrets_detailed,
    contains_secrets,
    mask_secret
)


class TestRedactSecrets:
    """Tests for the redact_secrets function."""
    
    def test_redact_api_key(self):
        """API keys should be redacted."""
        text = "api_key=sk-abcdefghij1234567890abcd"
        result = redact_secrets(text)
        assert "sk-abcdefghij1234567890abcd" not in result
        assert "[REDACTED]" in result
    
    def test_redact_bearer_token(self):
        """Bearer tokens should be redacted."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = redact_secrets(text)
        assert "eyJ" not in result
    
    def test_redact_aws_key(self):
        """AWS keys should be redacted."""
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = redact_secrets(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
    
    def test_redact_github_token(self):
        """GitHub tokens should be redacted."""
        text = "token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        result = redact_secrets(text)
        assert "ghp_" not in result
    
    def test_redact_private_key_header(self):
        """Private key headers should be redacted."""
        text = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBg..."
        result = redact_secrets(text)
        assert "-----BEGIN PRIVATE KEY-----" not in result
    
    def test_clean_text_unchanged(self):
        """Text without secrets should remain unchanged."""
        text = "This is a normal message about API design."
        result = redact_secrets(text)
        assert result == text
    
    def test_empty_input(self):
        """Empty input should return empty output."""
        assert redact_secrets("") == ""
        assert redact_secrets(None) is None


class TestRedactSecretsDetailed:
    """Tests for the redact_secrets_detailed function."""
    
    def test_returns_count_and_types(self):
        """Should return redaction count and types."""
        text = "api_key=abc123xyz789012345678901234567890"
        result = redact_secrets_detailed(text)
        assert result.redacted_count >= 1
        assert len(result.redaction_types) >= 1
    
    def test_multiple_secret_types(self):
        """Should identify multiple secret types."""
        text = "api_key=abc123xyz789012345678901234567890 token=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        result = redact_secrets_detailed(text)
        assert result.redacted_count >= 2


class TestContainsSecrets:
    """Tests for the contains_secrets function."""
    
    def test_detects_secrets(self):
        """Should detect presence of secrets."""
        assert contains_secrets("api_key=sk-12345678901234567890")
        assert contains_secrets("AKIAIOSFODNN7EXAMPLE")
    
    def test_no_secrets(self):
        """Should return False for clean text."""
        assert not contains_secrets("Hello world")
        assert not contains_secrets("Normal configuration")


class TestMaskSecret:
    """Tests for the mask_secret function."""
    
    def test_mask_with_default_visible(self):
        """Should show first 4 characters by default."""
        result = mask_secret("my-secret-api-key")
        assert result.startswith("my-s")
        assert "*" in result
    
    def test_mask_short_secret(self):
        """Short secrets should be fully masked."""
        result = mask_secret("abc")
        assert result == "***"
    
    def test_custom_visible_chars(self):
        """Should respect custom visible character count."""
        result = mask_secret("my-secret-key", visible_chars=6)
        assert result.startswith("my-sec")
