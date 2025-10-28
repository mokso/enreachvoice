"""
Custom exceptions for the EnreachVoice API client.
"""

from typing import Optional, Any


class EnreachAPIException(Exception):
    """
    Base exception for all EnreachVoice API errors.
    
    All exceptions raised by the EnreachVoice client inherit from this class,
    making it easy to catch all API-related errors.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code if applicable (e.g., 404, 500)
        response: Raw response body if available
        
    Example:
        >>> try:
        ...     client.get_usercalls(StartTime=start, EndTime=end)
        ... except EnreachAPIException as e:
        ...     print(f"API Error: {e}")
        ...     if e.status_code == 404:
        ...         print("Resource not found")
        ...     elif e.status_code >= 500:
        ...         print("Server error - try again later")
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        response: Optional[Any] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code if applicable
            response: Raw response body if available
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response
    
    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.status_code:
            return f"{self.message} (HTTP {self.status_code})"
        return self.message


class AuthenticationException(EnreachAPIException):
    """
    Raised when authentication fails.
    
    This exception indicates that the provided credentials are invalid or expired.
    When caught, the typical response is to re-authenticate or alert an administrator.
    
    This can happen when:
    - Invalid credentials (username/password)
    - Invalid or expired secret key
    - Missing authentication credentials
    - User account is locked or disabled
    
    Example:
        >>> try:
        ...     client = Client(username='user@example.com', secretkey='invalid')
        ... except AuthenticationException:
        ...     print("Authentication failed - check credentials")
        ...     # Re-authenticate or alert admin
    """
    pass


class RateLimitException(EnreachAPIException):
    """
    Raised when API rate limit is exceeded.
    
    The API has rate limits to prevent abuse. When this exception is raised,
    the typical response is to wait (using exponential backoff) before retrying.
    
    Example:
        >>> import time
        >>> try:
        ...     calls = client.get_usercalls(StartTime=start, EndTime=end)
        ... except RateLimitException:
        ...     print("Rate limit exceeded - waiting 60 seconds")
        ...     time.sleep(60)
        ...     calls = client.get_usercalls(StartTime=start, EndTime=end)
    """
    pass

