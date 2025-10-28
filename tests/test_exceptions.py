"""
Unit tests for enreachvoice custom exceptions.
"""

import pytest
from enreachvoice.exceptions import (
    EnreachAPIException,
    AuthenticationException,
    RateLimitException,
)


class TestEnreachAPIException:
    """Tests for the base EnreachAPIException class."""
    
    def test_basic_exception(self):
        """Test creating a basic exception with just a message."""
        exc = EnreachAPIException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.status_code is None
        assert exc.response is None
    
    def test_exception_with_status_code(self):
        """Test creating an exception with a status code."""
        exc = EnreachAPIException("Test error", status_code=500)
        assert str(exc) == "Test error (HTTP 500)"
        assert exc.status_code == 500
    
    def test_exception_with_response(self):
        """Test creating an exception with response data."""
        response_data = {"error": "Something went wrong"}
        exc = EnreachAPIException("Test error", status_code=400, response=response_data)
        assert exc.response == response_data
        assert exc.status_code == 400
    
    def test_generic_http_errors_via_status_code(self):
        """Test that generic HTTP errors can be checked via status_code."""
        # 404 Not Found
        exc_404 = EnreachAPIException("Not found", status_code=404)
        assert exc_404.status_code == 404
        
        # 500 Server Error
        exc_500 = EnreachAPIException("Server error", status_code=500)
        assert exc_500.status_code == 500


class TestAuthenticationException:
    """Tests for AuthenticationException."""
    
    def test_inheritance(self):
        """Test that AuthenticationException inherits from EnreachAPIException."""
        exc = AuthenticationException("Auth failed")
        assert isinstance(exc, EnreachAPIException)
    
    def test_with_status_code(self):
        """Test AuthenticationException with status code."""
        exc = AuthenticationException("Invalid credentials", status_code=401)
        assert str(exc) == "Invalid credentials (HTTP 401)"
        assert exc.status_code == 401


class TestRateLimitException:
    """Tests for RateLimitException."""
    
    def test_inheritance(self):
        """Test that RateLimitException inherits from EnreachAPIException."""
        exc = RateLimitException("Rate limit exceeded")
        assert isinstance(exc, EnreachAPIException)
    
    def test_with_status_code(self):
        """Test RateLimitException with 429 status code."""
        exc = RateLimitException("Rate limit exceeded", status_code=429)
        assert str(exc) == "Rate limit exceeded (HTTP 429)"
