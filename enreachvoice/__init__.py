"""
EnreachVoice Python Client Library

This library provides a Python interface to the EnreachVoice REST API.

Example usage:
    >>> from enreachvoice import Client
    >>> client = Client(username='user@example.com', secretkey='your-secret-key')
    >>> calls = client.get_usercalls(StartTime=start, EndTime=end)
"""

from .client import Client
from .exceptions import (
    EnreachAPIException,
    AuthenticationException,
    RateLimitException,
)
from .types import (
    TagSelection,
    ClassificationInstance,
    ClassifiedType,
)

__version__ = '0.2.0'
__all__ = [
    'Client',
    'EnreachAPIException',
    'AuthenticationException',
    'RateLimitException',
    'TagSelection',
    'ClassificationInstance',
    'ClassifiedType',
]
