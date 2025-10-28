"""
Type definitions for the EnreachVoice API client.

This module contains TypedDict definitions and type aliases used throughout
the EnreachVoice client library for better type safety and IDE support.
"""

from typing import TypedDict, List, Literal


class TagSelection(TypedDict, total=False):
    """
    Selected tag in a classification.
    
    Attributes:
        TagId: ID of the selected tag (required for creation)
        TagName: Name of the tag (read-only, returned by API)
        TagGroupId: ID of the tag's group (read-only, returned by API)
        TagGroupName: Name of the tag's group (read-only, returned by API)
    """
    TagId: int
    TagName: str
    TagGroupId: int
    TagGroupName: str


class ClassificationInstance(TypedDict, total=False):
    """
    A classification applied to a call or callback item.
    
    Attributes:
        Id: Unique identifier for the classification instance
        TagSchemaId: ID of the schema used for classification
        TagSchemaName: Name of the schema (read-only)
        TagSelections: List of selected tags
        Note: Optional free-text note (max 500 characters)
        CallId: ID of the classified call (for DirectCall/ServiceCall)
        CallListItemId: ID of the classified callback item (for CallListItem)
        ClassifiedTypeId: Numeric type ID
        ClassifiedType: Type of item being classified
        CreatedBy: User who created the classification (read-only)
        ModifiedBy: User who last modified the classification (read-only)
        Modified: Last modification timestamp (read-only)
    """
    Id: str
    TagSchemaId: str
    TagSchemaName: str
    TagSelections: List[TagSelection]
    Note: str
    CallId: str
    CallListItemId: str
    ClassifiedTypeId: int
    ClassifiedType: str
    CreatedBy: str
    ModifiedBy: str
    Modified: str


ClassifiedType = Literal[
    "Undefined",
    "None",
    "DirectCall",
    "ServiceCall",
    "Email",
    "CallListItem"
]
"""
Valid classification types for the ClassifiedType field.

- Undefined: Type not specified
- None: No classification type
- DirectCall: Direct call to a user
- ServiceCall: Call handled by a queue/service
- Email: Email communication
- CallListItem: Callback list item
"""
