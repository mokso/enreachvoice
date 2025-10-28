# EnreachVoice Python Client


An unofficial Python client library for the [EnreachVoice REST API](https://doc.enreachvoice.com/beneapi/). This library provides a clean, type-hinted interface for interacting with EnreachVoice API.


## Quick Start

### Authentication with Secret Key

```python
from enreachvoice import Client

# Initialize client with secret key
client = Client(
    username='user@example.com',
    secretkey='your-secret-key'
)

# Get user ID
print(f"Authenticated as user: {client.userid}")
```

### Authentication with Password

```python
from enreachvoice import Client

# Initialize client with password (secret key will be retrieved automatically)
client = Client(
    username='user@example.com',
    password='your-password'
)
```

### Using Test Environments

```python
from enreachvoice import Client

# Option 1: Use custom discovery URL for test environment
client = Client(
    username='user@example.com',
    secretkey='your-secret-key',
    discovery_url='https://discover-test.enreachvoice.com'
)

# Option 2: Bypass discovery and connect directly to API endpoint
client = Client(
    username='user@example.com',
    secretkey='your-secret-key',
    api_endpoint='https://api-test.enreachvoice.com'
)
```

## Usage Examples

### Retrieve Call History

```python
from datetime import datetime, timezone, timedelta
from enreachvoice import Client

client = Client(username='user@example.com', secretkey='your-secret-key')

# Get calls from the last 7 days
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(days=7)

calls = client.get_usercalls(
    StartTime=start_time,
    EndTime=end_time
)

print(f"Retrieved {len(calls)} calls")
for call in calls:
    print(f"Call ID: {call['CallId']}, Start: {call['StartTime']}")
```

### Get Specific Call by ID

```python
calls = client.get_usercalls(CallId='specific-call-id')
```

### Retrieve Queue Calls (Service Calls)

```python
from datetime import datetime, timezone, timedelta

client = Client(username='user@example.com', secretkey='your-secret-key')

end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(days=1)

queue_calls = client.get_inbound_queuecalls(
    StartTime=start_time,
    EndTime=end_time
)

for call in queue_calls:
    print(f"Queue: {call.get('QueueName')}, Duration: {call.get('Duration')}")
```

### Download Call Recording

```python
client = Client(username='user@example.com', secretkey='your-secret-key')

# Download recording to specified directory
client.get_recording_file(
    recordingId='recording-id-here',
    path='./recordings'
)
# File will be saved as ./recordings/recording-id-here.mp3
```

### Get Call Transcript

```python
client = Client(username='user@example.com', secretkey='your-secret-key')

# Get transcript (will wait if status is 'Pending')
transcript = client.get_transcript(
    transcriptId='transcript-id-here',
    wait_pending=True  # Wait for pending transcripts to complete
)

print(f"Transcript Status: {transcript['TranscriptStatus']}")
if transcript['TranscriptStatus'] == 'Completed':
    print(f"Text: {transcript['Text']}")
```

### Classification Management

EnreachVoice allows you to classify calls with structured tags. Classifications help categorize and analyze call data.

#### Get Available Classification Schemas

```python
client = Client(username='user@example.com', secretkey='your-secret-key')

# Get all schemas with their groups and tags
schemas = client.get_classification_schemas(include_children=True)

for schema in schemas:
    print(f"\nSchema: {schema['Name']}")
    for group in schema.get('Groups', []):
        print(f"  Group: {group['Name']} (Min: {group['MinSelections']}, Max: {group['MaxSelections']})")
        for tag in group.get('Tags', []):
            print(f"    [{tag['Id']}] {tag['Name']}")
```

#### Get Queue-Schema Mappings

```python
client = Client(username='user@example.com', secretkey='your-secret-key')

# Get mappings of queues to classification schemas
queue_schemas = client.get_queue_schemas()

for qs in queue_schemas:
    print(f"Queue: {qs['QueueName']} → Schema: {qs['SchemaId']}")

# Build a lookup dictionary for quick access
queue_to_schema = {qs['QueueId']: qs['SchemaId'] for qs in queue_schemas}

# Use it to find the right schema for a call's queue
call_queue_id = call['AnswerQueueId']
schema_id = queue_to_schema.get(call_queue_id)
```

#### Get Callback List-Schema Mappings

```python
client = Client(username='user@example.com', secretkey='your-secret-key')

# Get mappings of callback lists to classification schemas
calllist_schemas = client.get_calllist_schemas()

for cls in calllist_schemas:
    print(f"List: {cls['ListName']} → Schema: {cls['SchemaId']}")
    if cls.get('RequestTypeId'):
        print(f"  Request Type: {cls['RequestTypeId']}")

# Build a lookup dictionary for quick access
list_to_schema = {cls['ListId']: cls['SchemaId'] for cls in calllist_schemas}

# Use it to find the right schema for a callback item's list
callback_list_id = callback_item['CallbackListId']
schema_id = list_to_schema.get(callback_list_id)
```

#### Classify a Call

```python
from datetime import datetime, timezone, timedelta

client = Client(username='user@example.com', secretkey='your-secret-key')

# Get recent calls
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(hours=1)
calls = client.get_usercalls(StartTime=start_time, EndTime=end_time)

if calls:
    call = calls[0]
    
    # Create classification with selected tags
    classification = client.create_classification(
        call_id=call['CallId'],
        schema_id='2b2b9f78-4e01-4486-ab11-710c6be701c4',  # Your schema ID
        tag_selections=[
            {"TagId": 19},  # e.g., "Billing"
            {"TagId": 23},  # e.g., "Customer"
            {"TagId": 17}   # e.g., "Resolved"
        ],
        note="Customer billing inquiry about invoice #12345"
    )
    
    print(f"Classification created: {classification['Id']}")
```

#### Retrieve Call Classifications

```python
client = Client(username='user@example.com', secretkey='your-secret-key')

# Get classification for a specific call
classification = client.get_call_classification(call_id='4b415288-8604-4b6c-b604-e4eaeb90c938')

if classification:
    print(f"Schema: {classification['TagSchemaName']}")
    print("Selected tags:")
    for selection in classification['TagSelections']:
        print(f"  {selection['TagGroupName']}: {selection['TagName']}")
    
    if classification.get('Note'):
        print(f"Note: {classification['Note']}")
else:
    print("Call not classified")

# Or find all classifications for a call
classifications = client.find_classifications(call_id='4b415288-8604-4b6c-b604-e4eaeb90c938')
print(f"Found {len(classifications)} classification(s)")
```

#### Get Classification with Pretty-Printed Tag Names

```python
client = Client(username='user@example.com', secretkey='your-secret-key')

# Get classification with human-readable tag names
classification = client.get_call_classification_pretty(call_id='4b415288-8604-4b6c-b604-e4eaeb90c938')

if classification:
    print(f"Classification ID: {classification['Id']}")
    print(f"Schema: {classification['TagSchemaId']}")
    
    # The TagsPretty field provides a clean dictionary format
    print("\nTags (pretty-printed):")
    print(classification['TagsPretty'])
    # Output example:
    # {
    #   'Reason for call': 'Sales demo',
    #   'Customer type': 'Prospect',
    #   'Products': ['Hammers', 'Screwdrivers']
    # }
    
    # Access individual tags easily
    reason = classification['TagsPretty'].get('Reason for call')
    customer_type = classification['TagsPretty'].get('Customer type')
    products = classification['TagsPretty'].get('Products', [])
    
    print(f"\nReason: {reason}")
    print(f"Customer type: {customer_type}")
    print(f"Products: {', '.join(products)}")
```

#### Complete Classification Workflow

```python
from datetime import datetime, timezone, timedelta
from enreachvoice import Client

client = Client(username='user@example.com', secretkey='your-secret-key')

# Step 1: Get the classification schema
schema = client.get_classification_schema(
    schema_id='2b2b9f78-4e01-4486-ab11-710c6be701c4',
    include_children=True
)

print(f"Using schema: {schema['Name']}")

# Step 2: Get calls to classify
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(hours=1)
calls = client.get_usercalls(StartTime=start_time, EndTime=end_time)

# Step 3: Classify each call
for call in calls:
    # Check if already classified
    existing = client.get_call_classification(call['CallId'])
    
    if not existing:
        # Classify the call (in real app, user would select tags)
        classification = client.create_classification(
            call_id=call['CallId'],
            schema_id=schema['Id'],
            tag_selections=[
                {"TagId": 19},  # Based on schema tags
                {"TagId": 23}
            ],
            note=f"Auto-classified at {datetime.now()}"
        )
        print(f"Classified call {call['CallId'][:8]}...")

# Step 4: Generate report
print("\n=== Classification Report ===")
for call in calls:
    cls = client.get_call_classification(call['CallId'])
    if cls:
        tags = ", ".join([s['TagName'] for s in cls['TagSelections']])
        print(f"Call {call['CallId'][:8]}: {tags}")
```

## Error Handling

The library uses a minimal exception hierarchy focused on actionable error handling:

```python
from enreachvoice import Client
from enreachvoice import (
    AuthenticationException,
    RateLimitException,
    EnreachAPIException
)

try:
    client = Client(username='user@example.com', secretkey='invalid-key')
except AuthenticationException as e:
    print(f"Authentication failed: {e}")
    print(f"Status code: {e.status_code}")
    # Re-authenticate or alert admin

try:
    calls = client.get_usercalls()  # Missing required parameters
except ValueError as e:
    print(f"Invalid parameters: {e}")

try:
    # Check for specific HTTP errors using status_code
    calls = client.get_usercalls(CallId='nonexistent')
except EnreachAPIException as e:
    if e.status_code == 404:
        print("Call not found")
    elif e.status_code >= 500:
        print("Server error - retry later")
    else:
        print(f"API error {e.status_code}: {e}")

try:
    # Handle rate limiting with retry
    for i in range(1000):
        calls = client.get_usercalls(CallId=f'call-{i}')
except RateLimitException as e:
    print(f"Rate limit exceeded: {e}")
    import time
    time.sleep(60)  # Wait before retrying
```

