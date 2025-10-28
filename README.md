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

