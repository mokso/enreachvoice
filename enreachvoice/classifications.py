"""
Classification management for the EnreachVoice API client.

This module provides methods for managing call classifications, including
retrieving schemas, creating classifications, and querying existing classifications.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, cast


class ClassificationMixin:
    """
    Mixin class providing classification management methods for the EnreachVoice Client.
    
    This mixin adds methods for:
    - Retrieving classification schemas
    - Creating classifications for calls and callback items
    - Finding and querying existing classifications
    
    Note: This class requires the `invoke_api` method to be present in the class
    it's mixed into (provided by the Client class).
    """
    
    # Type stub for mypy - this method is provided by the Client class
    def invoke_api(
        self,
        path: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Stub for type checking - implemented in Client class."""
        raise NotImplementedError("This method is implemented in the Client class")
    
    def get_classification_schemas(
        self,
        include_children: bool = False,
        modified_after: Optional[datetime] = None,
        include_archived: bool = False,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all available classification schemas.
        
        Classification schemas define the structure of tags that can be applied to calls
        and callback items. Each schema contains groups of related tags.
        
        See: https://doc.enreachvoice.com/beneapi/#get-classification-schema
        
        Args:
            include_children: Include groups and tags in response (default: False)
            modified_after: Return only schemas modified after this time (optional)
            include_archived: Include archived schemas (default: False)
            include_deleted: Include deleted schemas (default: False)
            
        Returns:
            List of TagSchema objects
            
        Raises:
            AuthenticationException: If not authenticated
            EnreachAPIException: If API request fails
            
        Example:
            >>> schemas = client.get_classification_schemas(include_children=True)
            >>> for schema in schemas:
            ...     print(f"Schema: {schema['Name']}")
            ...     for group in schema.get('Groups', []):
            ...         print(f"  Group: {group['Name']}")
        """
        params: Dict[str, Any] = {
            'IncludeChildren': include_children,
            'IncludeArchived': include_archived,
            'IncludeDeleted': include_deleted,
        }
        
        if modified_after:
            params['ModifiedAfter'] = modified_after.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        result = self.invoke_api(
            method='GET',
            path='/classification/schemas',
            params=params
        )
        
        return cast(List[Dict[str, Any]], result)

    def get_classification_schema(
        self,schema_id: str,
        include_children: bool = False
    ) -> Dict[str, Any]:
        """
        Get a single classification schema by ID.
        
        See: https://doc.enreachvoice.com/beneapi/#get-classification-schema-schemaid
        
        Args:
            schema_id: Schema GUID
            include_children: Include groups and tags in response (default: False)
            
        Returns:
            TagSchema object with groups and tags if include_children=True
            
        Raises:
            AuthenticationException: If not authenticated
            EnreachAPIException: If schema not found or API request fails
            ValueError: If schema_id is empty
            
        Example:
            >>> schema = client.get_classification_schema(
            ...     schema_id="2b2b9f78-4e01-4486-ab11-710c6be701c4",
            ...     include_children=True
            ... )
            >>> print(f"Schema: {schema['Name']}")
            >>> print(f"Groups: {len(schema['Groups'])}")
        """
        if not schema_id:
            raise ValueError("schema_id is required")
        
        params = {'IncludeChildren': include_children}
        
        result = self.invoke_api(
            method='GET',
            path=f'/classification/schemas/{schema_id}',
            params=params
        )
        
        return result

    def create_classification(
        self,call_id: str,
        schema_id: str,
        tag_selections: List[Dict[str, int]],
        note: Optional[str] = None,
        classified_type: str = "ServiceCall"
    ) -> Dict[str, Any]:
        """
        Create a classification for a call or callback item.
        
        Classifications allow tagging calls with structured metadata using predefined schemas.
        Each classification consists of selected tags from various tag groups.
        
        See: https://doc.enreachvoice.com/beneapi/#post-classification-instance
        
        Args:
            call_id: GUID of the call to classify
            schema_id: GUID of the schema to use
            tag_selections: List of selected tags, e.g., [{"TagId": 19}, {"TagId": 23}]
            note: Optional free-text note (max 500 chars)
            classified_type: Type of item being classified (default: "ServiceCall")
                Options: "DirectCall", "ServiceCall", "Email", "CallListItem"
            
        Returns:
            Created ClassificationInstance with Id and full details
            
        Raises:
            AuthenticationException: If not authenticated
            EnreachAPIException: If classification creation fails
            ValueError: If required parameters are missing or invalid
            
        Example:
            >>> classification = client.create_classification(
            ...     call_id="4b415288-8604-4b6c-b604-e4eaeb90c938",
            ...     schema_id="2b2b9f78-4e01-4486-ab11-710c6be701c4",
            ...     tag_selections=[
            ...         {"TagId": 19},  # Billing
            ...         {"TagId": 23},  # Customer
            ...         {"TagId": 17}   # Yes
            ...     ],
            ...     note="Customer billing inquiry resolved"
            ... )
            >>> print(f"Classification created: {classification['Id']}")
        """
        if not call_id:
            raise ValueError("call_id is required")
        if not schema_id:
            raise ValueError("schema_id is required")
        if not tag_selections:
            raise ValueError("tag_selections cannot be empty")
        
        payload = {
            "TagSchemaId": schema_id,
            "TagSelections": tag_selections,
            "ClassifiedType": classified_type
        }
        
        if note:
            payload["Note"] = note
        
        # Determine which ID field to use based on classified_type
        if classified_type in ["DirectCall", "ServiceCall"]:
            payload["CallId"] = call_id
        elif classified_type == "CallListItem":
            payload["CallListItemId"] = call_id
        else:
            # Default to CallId for backward compatibility
            payload["CallId"] = call_id
        
        result = self.invoke_api(
            method='POST',
            path='/classification/instance',
            payload=payload
        )
        
        return result

    def find_classifications(
        self,call_id: Optional[str] = None,
        callback_list_item_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find classifications by call or callback item.
        
        At least one of call_id or callback_list_item_id must be provided.
        
        See: https://doc.enreachvoice.com/beneapi/#get-classification-instance-find
        
        Args:
            call_id: Filter by call GUID (optional)
            callback_list_item_id: Filter by callback list item GUID (optional)
            
        Returns:
            List of matching ClassificationInstance objects
            
        Raises:
            AuthenticationException: If not authenticated
            EnreachAPIException: If API request fails
            ValueError: If neither call_id nor callback_list_item_id is provided
            
        Example:
            >>> classifications = client.find_classifications(
            ...     call_id="4b415288-8604-4b6c-b604-e4eaeb90c938"
            ... )
            >>> for cls in classifications:
            ...     print(f"Schema: {cls['TagSchemaName']}")
            ...     for sel in cls['TagSelections']:
            ...         print(f"  {sel['TagGroupName']}: {sel['TagName']}")
        """
        if not call_id and not callback_list_item_id:
            raise ValueError("Either call_id or callback_list_item_id must be provided")
        
        params: Dict[str, str] = {}
        
        if call_id:
            params['CallId'] = call_id
        if callback_list_item_id:
            params['CallbackListItemId'] = callback_list_item_id
        
        result = self.invoke_api(
            method='GET',
            path='/classification/instance/',
            params=params
        )
        
        return cast(List[Dict[str, Any]], result)

    def get_call_classification(
        self,call_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the classification for a specific call (convenience method).
        
        This is a wrapper around find_classifications that returns the first
        classification found for the call, or None if no classification exists.
        
        Args:
            call_id: Call GUID
            
        Returns:
            ClassificationInstance or None if not classified
            
        Raises:
            AuthenticationException: If not authenticated
            EnreachAPIException: If API request fails
            ValueError: If call_id is empty
            
        Example:
            >>> classification = client.get_call_classification(call_id)
            >>> if classification:
            ...     print(f"Call classified as: {classification['TagSchemaName']}")
            ...     print(f"Note: {classification.get('Note', 'No note')}")
            >>> else:
            ...     print("Call not classified")
        """
        if not call_id:
            raise ValueError("call_id is required")
        
        classifications = self.find_classifications(call_id=call_id)
        
        return classifications[0] if classifications else None
    
    def get_call_classification_pretty(
        self,
        call_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the classification for a specific call with pretty-printed tag names.
        
        This method retrieves the classification and enriches it with a 'TagsPretty' field
        that contains a human-readable dictionary of group names to tag names.
        
        For groups with MaxSelections > 1, the value will be a list of tag names.
        For single-selection groups, the value will be a single string.
        
        Args:
            call_id: Call GUID
            
        Returns:
            ClassificationInstance with additional 'TagsPretty' field, or None if not classified
            
        Raises:
            AuthenticationException: If not authenticated
            EnreachAPIException: If API request fails
            ValueError: If call_id is empty
            
        Example:
            >>> classification = client.get_call_classification_pretty(call_id)
            >>> if classification:
            ...     print(classification['TagsPretty'])
            ...     # {'Reason for call': 'Sales demo', 
            ...     #  'Customer type': 'Prospect',
            ...     #  'Products': ['Hammers', 'Screwdrivers']}
        """
        if not call_id:
            raise ValueError("call_id is required")
        
        # Get the basic classification
        classification = self.get_call_classification(call_id)
        if not classification:
            return None
        
        # Get the full schema to map tag IDs to names
        schema_id = classification.get('TagSchemaId')
        if not schema_id:
            return classification
        
        schema = self.get_classification_schema(schema_id, include_children=True)
        if not schema:
            return classification
        
        # Build a mapping of tag IDs to their names and groups
        tag_map: Dict[int, Dict[str, Any]] = {}
        group_max_selections: Dict[str, int] = {}
        
        for group in schema.get('Groups', []):
            group_name = group.get('Name', 'Unknown Group')
            max_selections = group.get('MaxSelections', 1)
            group_max_selections[group_name] = max_selections
            
            for tag in group.get('Tags', []):
                tag_id = tag.get('Id')
                if tag_id:
                    tag_map[tag_id] = {
                        'name': tag.get('Name', 'Unknown Tag'),
                        'group': group_name
                    }
        
        # Build the pretty-printed dictionary
        tags_pretty: Dict[str, Any] = {}
        
        for selection in classification.get('TagSelections', []):
            tag_id = selection.get('TagId')
            if tag_id and tag_id in tag_map:
                tag_info = tag_map[tag_id]
                group_name = tag_info['group']
                tag_name = tag_info['name']
                
                # Check if this group allows multiple selections
                max_selections = group_max_selections.get(group_name, 1)
                
                if max_selections > 1:
                    # Multi-selection group - use a list
                    if group_name not in tags_pretty:
                        tags_pretty[group_name] = []
                    tags_pretty[group_name].append(tag_name)
                else:
                    # Single-selection group - use a string
                    tags_pretty[group_name] = tag_name
        
        # Add the pretty-printed tags to the classification
        classification['TagsPretty'] = tags_pretty
        
        return classification
    
    def get_queue_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all queue-schema bindings for the current user.
        
        Returns a list of mappings between service queues and classification schemas.
        Each binding indicates which classification schema should be used for calls
        from a specific queue.
        
        See: https://doc.enreachvoice.com/beneapi/#get-classification-queueschemas
        
        Returns:
            List of QueueSchema objects containing QueueId, SchemaId, QueueName
            
        Raises:
            AuthenticationException: If not authenticated
            EnreachAPIException: If API request fails
            
        Example:
            >>> queue_schemas = client.get_queue_schemas()
            >>> for qs in queue_schemas:
            ...     print(f"Queue: {qs['QueueName']} (ID: {qs['QueueId']})")
            ...     print(f"  Schema ID: {qs['SchemaId']}")
        """
        result = self.invoke_api(
            method='GET',
            path='/classification/queueschemas'
        )
        
        return cast(List[Dict[str, Any]], result)
    
    def get_calllist_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all callback list-schema bindings for the current user.
        
        Returns a list of mappings between callback lists and classification schemas.
        Each binding indicates which classification schema should be used for items
        in a specific callback list.
        
        See: https://doc.enreachvoice.com/beneapi/#get-classification-calllistschemas
        
        Returns:
            List of CallbackListSchema objects containing ListId, SchemaId, ListName, 
            RequestTypeId (optional)
            
        Raises:
            AuthenticationException: If not authenticated
            EnreachAPIException: If API request fails
            
        Example:
            >>> calllist_schemas = client.get_calllist_schemas()
            >>> for cls in calllist_schemas:
            ...     print(f"List: {cls['ListName']} (ID: {cls['ListId']})")
            ...     print(f"  Schema ID: {cls['SchemaId']}")
            ...     if cls.get('RequestTypeId'):
            ...         print(f"  Request Type: {cls['RequestTypeId']}")
        """
        result = self.invoke_api(
            method='GET',
            path='/classification/calllistschemas'
        )
        
        return cast(List[Dict[str, Any]], result)
