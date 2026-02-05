"""
Tests for the input validator module.
"""

import pytest
from security.input_validator import (
    validate_user_request,
    validate_constraints,
    validate_context,
    sanitize_text,
    is_safe_url
)


class TestValidateUserRequest:
    """Tests for the validate_user_request function."""
    
    def test_valid_request(self):
        """Normal requests should pass validation."""
        result = validate_user_request("Write a Python function to sort a list")
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_empty_request_rejected(self):
        """Empty requests should be rejected."""
        result = validate_user_request("")
        assert not result.is_valid
        
        result = validate_user_request("   ")
        assert not result.is_valid
    
    def test_control_chars_removed(self):
        """Control characters should be stripped."""
        result = validate_user_request("Hello\x00World\x1fTest")
        assert result.is_valid
        assert "\x00" not in result.sanitized_text
        assert "\x1f" not in result.sanitized_text
    
    def test_size_limit_enforced(self):
        """Requests exceeding size limit should be rejected."""
        huge_request = "x" * 50000  # Much larger than 10KB
        result = validate_user_request(huge_request)
        assert not result.is_valid
        assert any("size" in e.lower() for e in result.errors)
    
    def test_short_request_warning(self):
        """Very short requests should produce a warning."""
        result = validate_user_request("hi")
        assert result.is_valid
        assert any("short" in w.lower() for w in result.warnings)


class TestValidateConstraints:
    """Tests for the validate_constraints function."""
    
    def test_valid_constraints(self):
        """Normal constraints should pass."""
        constraints = ["Must be efficient", "Should handle errors"]
        result = validate_constraints(constraints)
        assert result.is_valid
    
    def test_empty_constraints_ok(self):
        """Empty constraint list should be valid."""
        result = validate_constraints([])
        assert result.is_valid
    
    def test_long_constraint_warning(self):
        """Very long constraints should produce warning."""
        constraints = ["x" * 600]
        result = validate_constraints(constraints)
        assert result.is_valid
        assert len(result.warnings) > 0


class TestValidateContext:
    """Tests for the validate_context function."""
    
    def test_valid_context(self):
        """Normal context should pass."""
        result = validate_context("This is a web application project")
        assert result.is_valid
    
    def test_empty_context_ok(self):
        """Empty/None context should be valid."""
        result = validate_context(None)
        assert result.is_valid
        
        result = validate_context("")
        assert result.is_valid


class TestSanitizeText:
    """Tests for the sanitize_text function."""
    
    def test_removes_null_bytes(self):
        """Null bytes should be removed."""
        result = sanitize_text("Hello\x00World")
        assert "\x00" not in result
    
    def test_normalizes_whitespace(self):
        """Excessive whitespace should be normalized."""
        result = sanitize_text("Hello                    World")
        assert "                    " not in result
    
    def test_strips_edges(self):
        """Leading/trailing whitespace should be stripped."""
        result = sanitize_text("   Hello World   ")
        assert result == "Hello World"


class TestIsSafeUrl:
    """Tests for the is_safe_url function."""
    
    def test_https_urls_safe(self):
        """HTTPS URLs should be considered safe."""
        assert is_safe_url("https://example.com")
        assert is_safe_url("https://api.github.com/repos")
    
    def test_localhost_blocked(self):
        """Localhost should be blocked."""
        assert not is_safe_url("http://localhost:8080")
        assert not is_safe_url("http://127.0.0.1")
    
    def test_private_ips_blocked(self):
        """Private IP ranges should be blocked."""
        assert not is_safe_url("http://10.0.0.1")
        assert not is_safe_url("http://192.168.1.1")
        assert not is_safe_url("http://172.16.0.1")
    
    def test_file_protocol_blocked(self):
        """File protocol should be blocked."""
        assert not is_safe_url("file:///etc/passwd")
    
    def test_internal_hostnames_blocked(self):
        """Internal hostname patterns should be blocked."""
        assert not is_safe_url("http://internal.company.com")
        assert not is_safe_url("http://intranet.local")
