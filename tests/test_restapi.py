"""
Unit tests for the EnreachVoice API Client.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from enreachvoice.client import Client, HEADERS, DISCOVERY_URL
from enreachvoice.exceptions import (
    EnreachAPIException,
    AuthenticationException,
    RateLimitException,
)


class TestClientInit:
    """Tests for Client initialization."""
    
    @patch('enreachvoice.client.requests.get')
    def test_init_with_secretkey(self, mock_get):
        """Test client initialization with secretkey."""
        # Mock discovery response
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = [{'apiEndpoint': 'https://api.test.com/'}]
        
        # Mock users/me response
        user_response = Mock()
        user_response.status_code = 200
        user_response.ok = True
        user_response.json.return_value = {'Id': 'test-user-id'}
        
        mock_get.side_effect = [discovery_response, user_response]
        
        client = Client(username='test@example.com', secretkey='test-key')
        
        assert client.username == 'test@example.com'
        assert client.secretkey == 'test-key'
        assert client.userid == 'test-user-id'
        assert client.apiEndpoint == 'https://api.test.com'
    
    @patch('enreachvoice.client.requests.post')
    @patch('enreachvoice.client.requests.get')
    def test_init_with_password(self, mock_get, mock_post):
        """Test client initialization with password."""
        # Mock discovery response
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = [{'apiEndpoint': 'https://api.test.com/'}]
        
        # Mock authentication response
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {'SecretKey': 'generated-key'}
        
        # Mock users/me response
        user_response = Mock()
        user_response.status_code = 200
        user_response.ok = True
        user_response.json.return_value = {'Id': 'test-user-id'}
        
        mock_post.return_value = auth_response
        mock_get.side_effect = [discovery_response, user_response]
        
        client = Client(username='test@example.com', password='test-password')
        
        assert client.username == 'test@example.com'
        assert client.secretkey == 'generated-key'
        assert client.userid == 'test-user-id'
    
    @patch('enreachvoice.client.requests.get')
    def test_init_without_credentials(self, mock_get):
        """Test that initialization fails without secretkey or password."""
        # Mock discovery response
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = [{'apiEndpoint': 'https://api.test.com/'}]
        mock_get.return_value = discovery_response
        
        with pytest.raises(ValueError) as exc_info:
            Client(username='test@example.com')
        
        assert "Either secretkey or password must be provided" in str(exc_info.value)
    
    @patch('enreachvoice.client.requests.get')
    def test_init_discovery_failure(self, mock_get):
        """Test that initialization fails when discovery fails."""
        # Mock failed discovery response
        discovery_response = Mock()
        discovery_response.status_code = 500
        discovery_response.text = "Internal Server Error"
        mock_get.return_value = discovery_response
        
        with pytest.raises(EnreachAPIException):
            Client(username='test@example.com', secretkey='test-key')
    
    @patch('enreachvoice.client.requests.get')
    def test_init_with_custom_discovery_url(self, mock_get):
        """Test client initialization with custom discovery URL."""
        # Mock discovery response
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = [{'apiEndpoint': 'https://api-test.enreachvoice.com/'}]
        
        # Mock users/me response
        user_response = Mock()
        user_response.status_code = 200
        user_response.ok = True
        user_response.json.return_value = {'Id': 'test-user-id'}
        
        mock_get.side_effect = [discovery_response, user_response]
        
        client = Client(
            username='test@example.com',
            secretkey='test-key',
            discovery_url='https://discover-test.enreachvoice.com'
        )
        
        assert client.discovery_url == 'https://discover-test.enreachvoice.com'
        assert client.apiEndpoint == 'https://api-test.enreachvoice.com'
        
        # Verify discovery was called with custom URL
        discovery_call = mock_get.call_args_list[0]
        assert 'discover-test.enreachvoice.com' in discovery_call[0][0]
    
    @patch('enreachvoice.client.requests.get')
    def test_init_with_direct_api_endpoint(self, mock_get):
        """Test client initialization with direct API endpoint (bypasses discovery)."""
        # Mock users/me response only (no discovery call expected)
        user_response = Mock()
        user_response.status_code = 200
        user_response.ok = True
        user_response.json.return_value = {'Id': 'test-user-id'}
        
        mock_get.return_value = user_response
        
        client = Client(
            username='test@example.com',
            secretkey='test-key',
            api_endpoint='https://api-test.enreachvoice.com'
        )
        
        assert client.apiEndpoint == 'https://api-test.enreachvoice.com'
        
        # Verify discovery was NOT called (only users/me was called)
        assert mock_get.call_count == 1
        assert 'users/me' in str(mock_get.call_args)
    
    @patch('enreachvoice.client.requests.get')
    def test_init_with_api_endpoint_strips_trailing_slash(self, mock_get):
        """Test that direct API endpoint removes trailing slash."""
        user_response = Mock()
        user_response.status_code = 200
        user_response.ok = True
        user_response.json.return_value = {'Id': 'test-user-id'}
        
        mock_get.return_value = user_response
        
        client = Client(
            username='test@example.com',
            secretkey='test-key',
            api_endpoint='https://api-test.enreachvoice.com/'
        )
        
        assert client.apiEndpoint == 'https://api-test.enreachvoice.com'


class TestGetApiUrl:
    """Tests for get_apiurl method."""
    
    @patch('enreachvoice.client.requests.get')
    def test_successful_discovery(self, mock_get):
        """Test successful API endpoint discovery."""
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = [{'apiEndpoint': 'https://api.test.com/'}]
        mock_get.return_value = discovery_response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.discovery_url = DISCOVERY_URL
        
        result = client.get_apiurl()
        
        assert result == 'https://api.test.com'
        mock_get.assert_called_once_with(f"{DISCOVERY_URL}/api/user?user=test@example.com")
    
    @patch('enreachvoice.client.requests.get')
    def test_discovery_removes_trailing_slash(self, mock_get):
        """Test that trailing slash is removed from API endpoint."""
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = [{'apiEndpoint': 'https://api.test.com/'}]
        mock_get.return_value = discovery_response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.discovery_url = DISCOVERY_URL
        
        result = client.get_apiurl()
        
        assert result == 'https://api.test.com'
    
    @patch('enreachvoice.client.requests.get')
    def test_discovery_error_status(self, mock_get):
        """Test discovery failure with error status."""
        discovery_response = Mock()
        discovery_response.status_code = 404
        discovery_response.text = "Not Found"
        mock_get.return_value = discovery_response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.discovery_url = DISCOVERY_URL
        
        with pytest.raises(EnreachAPIException) as exc_info:
            client.get_apiurl()
        
        assert "404" in str(exc_info.value)


class TestInvokeAPI:
    """Tests for invoke_api method."""
    
    @patch('enreachvoice.client.requests.get')
    def test_successful_get_request(self, mock_get):
        """Test successful GET request."""
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.json.return_value = {'result': 'success'}
        mock_get.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.invoke_api('/test', method='GET')
        
        assert result == {'result': 'success'}
    
    @patch('enreachvoice.client.requests.post')
    def test_successful_post_request(self, mock_post):
        """Test successful POST request."""
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.json.return_value = {'created': 'true'}
        mock_post.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.invoke_api('/test', method='POST', payload={'data': 'value'})
        
        assert result == {'created': 'true'}
    
    def test_invalid_method(self):
        """Test that invalid HTTP method raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError) as exc_info:
            client.invoke_api('/test', method='PATCH')
        
        assert "Invalid method" in str(exc_info.value)
    
    def test_missing_path(self):
        """Test that missing path raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError) as exc_info:
            client.invoke_api(None)
        
        assert "Path must be provided" in str(exc_info.value)
    
    @patch('enreachvoice.client.requests.get')
    def test_401_raises_authentication_exception(self, mock_get):
        """Test that 401 status raises AuthenticationException."""
        response = Mock()
        response.status_code = 401
        response.ok = False
        response.json.return_value = {'error': 'Unauthorized'}
        mock_get.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(AuthenticationException) as exc_info:
            client.invoke_api('/test')
        
        assert exc_info.value.status_code == 401
    
    @patch('enreachvoice.client.requests.get')
    def test_404_raises_enreach_api_exception(self, mock_get):
        """Test that 404 status raises EnreachAPIException with status_code."""
        response = Mock()
        response.status_code = 404
        response.ok = False
        response.json.return_value = {'error': 'Not Found'}
        mock_get.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(EnreachAPIException) as exc_info:
            client.invoke_api('/test')
        
        assert exc_info.value.status_code == 404
    
    @patch('enreachvoice.client.requests.get')
    def test_429_raises_rate_limit_exception(self, mock_get):
        """Test that 429 status raises RateLimitException."""
        response = Mock()
        response.status_code = 429
        response.ok = False
        response.json.return_value = {'error': 'Rate limit exceeded'}
        mock_get.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(RateLimitException) as exc_info:
            client.invoke_api('/test')
        
        assert exc_info.value.status_code == 429
    
    @patch('enreachvoice.client.requests.get')
    def test_invalid_json_raises_exception(self, mock_get):
        """Test that invalid JSON response raises EnreachAPIException."""
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.json.side_effect = ValueError("Invalid JSON")
        response.text = "Not valid JSON"
        mock_get.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(EnreachAPIException):
            client.invoke_api('/test')


class TestAuthenticateWithPassword:
    """Tests for authenticate_with_password method."""
    
    @patch('enreachvoice.client.requests.post')
    def test_successful_authentication(self, mock_post):
        """Test successful password authentication."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'SecretKey': 'generated-secret-key'}
        mock_post.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.authenticate_with_password('test-password')
        
        assert result == 'generated-secret-key'
    
    @patch('enreachvoice.client.requests.post')
    def test_failed_authentication(self, mock_post):
        """Test failed password authentication."""
        response = Mock()
        response.status_code = 401
        response.text = "Invalid credentials"
        mock_post.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(AuthenticationException):
            client.authenticate_with_password('wrong-password')


class TestGetUserCalls:
    """Tests for get_usercalls method."""
    
    @patch.object(Client, 'invoke_api')
    def test_get_calls_with_time_range(self, mock_invoke):
        """Test getting calls with StartTime and EndTime."""
        mock_invoke.return_value = [
            {'CallId': 'call1', 'StartTime': '2025-10-01 10:00:00'},
            {'CallId': 'call2', 'StartTime': '2025-10-01 11:00:00'}
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        start = datetime(2025, 10, 1, tzinfo=timezone.utc)
        end = datetime(2025, 10, 2, tzinfo=timezone.utc)
        
        result = client.get_usercalls(StartTime=start, EndTime=end)
        
        assert len(result) == 2
        assert result[0]['CallId'] == 'call1'
    
    @patch.object(Client, 'invoke_api')
    def test_get_calls_with_call_id(self, mock_invoke):
        """Test getting calls by CallId."""
        mock_invoke.return_value = [
            {'CallId': 'specific-call', 'StartTime': '2025-10-01 10:00:00'}
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_usercalls(CallId='specific-call')
        
        assert len(result) == 1
        assert result[0]['CallId'] == 'specific-call'
    
    def test_get_calls_without_filters_raises_exception(self):
        """Test that missing filter parameters raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError):
            client.get_usercalls()
    
    def test_get_calls_time_range_too_large(self):
        """Test that time range > 31 days raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        start = datetime(2025, 10, 1, tzinfo=timezone.utc)
        end = datetime(2025, 11, 10, tzinfo=timezone.utc)  # 40 days
        
        with pytest.raises(ValueError) as exc_info:
            client.get_usercalls(StartTime=start, EndTime=end)
        
        assert "31 days" in str(exc_info.value)


class TestGetInboundQueueCalls:
    """Tests for get_inbound_queuecalls method."""
    
    @patch.object(Client, 'invoke_api')
    def test_get_queue_calls(self, mock_invoke):
        """Test getting inbound queue calls."""
        mock_invoke.return_value = [
            {'ServiceCallId': 'sc1', 'QueueName': 'Support'},
            {'ServiceCallId': 'sc2', 'QueueName': 'Sales'}
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        start = datetime(2025, 10, 1, tzinfo=timezone.utc)
        end = datetime(2025, 10, 2, tzinfo=timezone.utc)
        
        result = client.get_inbound_queuecalls(StartTime=start, EndTime=end)
        
        assert len(result) == 2
    
    def test_get_queue_calls_without_filters_raises_exception(self):
        """Test that missing filter parameters raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError):
            client.get_inbound_queuecalls()


class TestGetRecordingFile:
    """Tests for get_recording_file method."""
    
    @patch('enreachvoice.client.os.makedirs')
    @patch('enreachvoice.client.requests.get')
    @patch('builtins.open', create=True)
    def test_successful_recording_download(self, mock_open, mock_get, mock_makedirs):
        """Test successful recording download."""
        # Mock recording metadata response
        metadata_response = Mock()
        metadata_response.status_code = 200
        metadata_response.json.return_value = {'URL': 'recordings/audio.mp3'}
        
        # Mock audio file response
        audio_response = Mock()
        audio_response.content = b'fake audio data'
        
        mock_get.side_effect = [metadata_response, audio_response]
        
        # Mock file writing
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        client.get_recording_file('recording123', '/tmp/recordings')
        
        mock_makedirs.assert_called_once_with('/tmp/recordings', exist_ok=True)
        mock_file.write.assert_called_once_with(b'fake audio data')
    
    @patch('enreachvoice.client.requests.get')
    def test_recording_download_failure(self, mock_get):
        """Test recording download failure."""
        response = Mock()
        response.status_code = 404
        response.text = "Recording not found"
        mock_get.return_value = response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(EnreachAPIException):
            client.get_recording_file('nonexistent', '/tmp')


class TestGetTranscript:
    """Tests for get_transcript method."""
    
    @patch.object(Client, 'invoke_api')
    def test_get_completed_transcript(self, mock_invoke):
        """Test getting a completed transcript."""
        mock_invoke.return_value = {
            'TranscriptId': 'trans123',
            'TranscriptStatus': 'Completed',
            'Text': 'Hello world'
        }
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_transcript('trans123')
        
        assert result['TranscriptStatus'] == 'Completed'
        assert result['Text'] == 'Hello world'
    
    @patch('enreachvoice.client.time.sleep')
    @patch.object(Client, 'invoke_api')
    def test_get_pending_transcript_wait(self, mock_invoke, mock_sleep):
        """Test waiting for a pending transcript to complete."""
        # First call returns Pending, second returns Completed
        mock_invoke.side_effect = [
            {'TranscriptId': 'trans123', 'TranscriptStatus': 'Pending'},
            {'TranscriptId': 'trans123', 'TranscriptStatus': 'Completed', 'Text': 'Done'}
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_transcript('trans123', wait_pending=True)
        
        assert result['TranscriptStatus'] == 'Completed'
        mock_sleep.assert_called_once()
    
    @patch.object(Client, 'invoke_api')
    def test_get_pending_transcript_no_wait(self, mock_invoke):
        """Test getting pending transcript without waiting."""
        mock_invoke.return_value = {
            'TranscriptId': 'trans123',
            'TranscriptStatus': 'Pending'
        }
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_transcript('trans123', wait_pending=False)
        
        assert result['TranscriptStatus'] == 'Pending'


class TestClassificationMethods:
    """Tests for classification methods."""
    
    @patch.object(Client, 'invoke_api')
    def test_get_classification_schemas(self, mock_invoke):
        """Test getting all classification schemas."""
        mock_invoke.return_value = [
            {
                'Id': 'schema-1',
                'Name': 'Call Classification',
                'Description': 'Standard call classification'
            },
            {
                'Id': 'schema-2',
                'Name': 'Support Classification',
                'Description': 'Support ticket classification'
            }
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_classification_schemas()
        
        assert len(result) == 2
        assert result[0]['Name'] == 'Call Classification'
        mock_invoke.assert_called_once_with(
            method='GET',
            path='/classification/schemas',
            params={
                'IncludeChildren': False,
                'IncludeArchived': False,
                'IncludeDeleted': False
            }
        )
    
    @patch.object(Client, 'invoke_api')
    def test_get_classification_schemas_with_children(self, mock_invoke):
        """Test getting schemas with children (groups and tags)."""
        mock_invoke.return_value = [
            {
                'Id': 'schema-1',
                'Name': 'Call Classification',
                'Groups': [
                    {
                        'Id': 1,
                        'Name': 'Category',
                        'Tags': [
                            {'Id': 10, 'Name': 'Billing'},
                            {'Id': 11, 'Name': 'Support'}
                        ]
                    }
                ]
            }
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_classification_schemas(include_children=True)
        
        assert len(result[0]['Groups']) == 1
        assert len(result[0]['Groups'][0]['Tags']) == 2
        mock_invoke.assert_called_once_with(
            method='GET',
            path='/classification/schemas',
            params={
                'IncludeChildren': True,
                'IncludeArchived': False,
                'IncludeDeleted': False
            }
        )
    
    @patch.object(Client, 'invoke_api')
    def test_get_classification_schemas_with_modified_after(self, mock_invoke):
        """Test getting schemas filtered by modified date."""
        mock_invoke.return_value = []
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        modified_date = datetime(2025, 1, 1, 12, 0, 0)
        client.get_classification_schemas(modified_after=modified_date)
        
        call_args = mock_invoke.call_args
        assert 'ModifiedAfter' in call_args[1]['params']
        assert call_args[1]['params']['ModifiedAfter'].startswith('2025-01-01')
    
    @patch.object(Client, 'invoke_api')
    def test_get_classification_schema(self, mock_invoke):
        """Test getting a single classification schema."""
        mock_invoke.return_value = {
            'Id': 'schema-1',
            'Name': 'Call Classification',
            'Description': 'Standard call classification'
        }
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_classification_schema('schema-1')
        
        assert result['Id'] == 'schema-1'
        assert result['Name'] == 'Call Classification'
        mock_invoke.assert_called_once_with(
            method='GET',
            path='/classification/schemas/schema-1',
            params={'IncludeChildren': False}
        )
    
    @patch.object(Client, 'invoke_api')
    def test_get_classification_schema_with_children(self, mock_invoke):
        """Test getting schema with groups and tags."""
        mock_invoke.return_value = {
            'Id': 'schema-1',
            'Name': 'Call Classification',
            'Groups': [
                {
                    'Id': 1,
                    'Name': 'Category',
                    'MinSelections': 1,
                    'MaxSelections': 1,
                    'Tags': [
                        {'Id': 10, 'Name': 'Billing', 'StyleEnum': 'Primary'},
                        {'Id': 11, 'Name': 'Support', 'StyleEnum': 'Success'}
                    ]
                }
            ]
        }
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_classification_schema('schema-1', include_children=True)
        
        assert len(result['Groups']) == 1
        assert result['Groups'][0]['MinSelections'] == 1
        assert len(result['Groups'][0]['Tags']) == 2
    
    def test_get_classification_schema_empty_id(self):
        """Test that empty schema_id raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError) as exc_info:
            client.get_classification_schema('')
        
        assert "schema_id is required" in str(exc_info.value)
    
    @patch.object(Client, 'invoke_api')
    def test_create_classification(self, mock_invoke):
        """Test creating a classification for a call."""
        mock_invoke.return_value = {
            'Id': 'classification-123',
            'TagSchemaId': 'schema-1',
            'TagSchemaName': 'Call Classification',
            'CallId': 'call-456',
            'TagSelections': [
                {'TagId': 10, 'TagName': 'Billing', 'TagGroupId': 1, 'TagGroupName': 'Category'},
                {'TagId': 23, 'TagName': 'Customer', 'TagGroupId': 2, 'TagGroupName': 'Type'}
            ],
            'Note': 'Test note',
            'ClassifiedType': 'ServiceCall'
        }
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.create_classification(
            call_id='call-456',
            schema_id='schema-1',
            tag_selections=[{'TagId': 10}, {'TagId': 23}],
            note='Test note'
        )
        
        assert result['Id'] == 'classification-123'
        assert result['CallId'] == 'call-456'
        assert len(result['TagSelections']) == 2
        
        # Verify the API call
        call_args = mock_invoke.call_args
        assert call_args[1]['method'] == 'POST'
        assert call_args[1]['path'] == '/classification/instance'
        
        payload = call_args[1]['payload']
        assert payload['TagSchemaId'] == 'schema-1'
        assert payload['CallId'] == 'call-456'
        assert payload['Note'] == 'Test note'
        assert payload['ClassifiedType'] == 'ServiceCall'
        assert len(payload['TagSelections']) == 2
    
    @patch.object(Client, 'invoke_api')
    def test_create_classification_without_note(self, mock_invoke):
        """Test creating classification without optional note."""
        mock_invoke.return_value = {
            'Id': 'classification-123',
            'TagSchemaId': 'schema-1',
            'CallId': 'call-456',
            'TagSelections': [{'TagId': 10}]
        }
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.create_classification(
            call_id='call-456',
            schema_id='schema-1',
            tag_selections=[{'TagId': 10}]
        )
        
        assert result['Id'] == 'classification-123'
        
        # Verify Note is not in payload when not provided
        payload = mock_invoke.call_args[1]['payload']
        assert 'Note' not in payload
    
    @patch.object(Client, 'invoke_api')
    def test_create_classification_direct_call(self, mock_invoke):
        """Test creating classification for DirectCall type."""
        mock_invoke.return_value = {'Id': 'classification-123'}
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        client.create_classification(
            call_id='call-456',
            schema_id='schema-1',
            tag_selections=[{'TagId': 10}],
            classified_type='DirectCall'
        )
        
        payload = mock_invoke.call_args[1]['payload']
        assert payload['ClassifiedType'] == 'DirectCall'
        assert payload['CallId'] == 'call-456'
    
    @patch.object(Client, 'invoke_api')
    def test_create_classification_callback_item(self, mock_invoke):
        """Test creating classification for CallListItem type."""
        mock_invoke.return_value = {'Id': 'classification-123'}
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        client.create_classification(
            call_id='item-789',
            schema_id='schema-1',
            tag_selections=[{'TagId': 10}],
            classified_type='CallListItem'
        )
        
        payload = mock_invoke.call_args[1]['payload']
        assert payload['ClassifiedType'] == 'CallListItem'
        assert payload['CallListItemId'] == 'item-789'
        assert 'CallId' not in payload
    
    def test_create_classification_missing_call_id(self):
        """Test that missing call_id raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError) as exc_info:
            client.create_classification(
                call_id='',
                schema_id='schema-1',
                tag_selections=[{'TagId': 10}]
            )
        
        assert "call_id is required" in str(exc_info.value)
    
    def test_create_classification_missing_schema_id(self):
        """Test that missing schema_id raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError) as exc_info:
            client.create_classification(
                call_id='call-456',
                schema_id='',
                tag_selections=[{'TagId': 10}]
            )
        
        assert "schema_id is required" in str(exc_info.value)
    
    def test_create_classification_empty_tag_selections(self):
        """Test that empty tag_selections raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError) as exc_info:
            client.create_classification(
                call_id='call-456',
                schema_id='schema-1',
                tag_selections=[]
            )
        
        assert "tag_selections cannot be empty" in str(exc_info.value)
    
    @patch.object(Client, 'invoke_api')
    def test_find_classifications_by_call_id(self, mock_invoke):
        """Test finding classifications by call ID."""
        mock_invoke.return_value = [
            {
                'Id': 'classification-123',
                'TagSchemaName': 'Call Classification',
                'CallId': 'call-456',
                'TagSelections': [
                    {'TagId': 10, 'TagName': 'Billing', 'TagGroupName': 'Category'}
                ]
            }
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.find_classifications(call_id='call-456')
        
        assert len(result) == 1
        assert result[0]['CallId'] == 'call-456'
        
        mock_invoke.assert_called_once_with(
            method='GET',
            path='/classification/instance/',
            params={'CallId': 'call-456'}
        )
    
    @patch.object(Client, 'invoke_api')
    def test_find_classifications_by_callback_item(self, mock_invoke):
        """Test finding classifications by callback list item ID."""
        mock_invoke.return_value = [
            {
                'Id': 'classification-789',
                'CallListItemId': 'item-123'
            }
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.find_classifications(callback_list_item_id='item-123')
        
        assert len(result) == 1
        assert result[0]['CallListItemId'] == 'item-123'
        
        mock_invoke.assert_called_once_with(
            method='GET',
            path='/classification/instance/',
            params={'CallbackListItemId': 'item-123'}
        )
    
    @patch.object(Client, 'invoke_api')
    def test_find_classifications_with_both_ids(self, mock_invoke):
        """Test finding classifications with both call and callback IDs."""
        mock_invoke.return_value = []
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        client.find_classifications(
            call_id='call-456',
            callback_list_item_id='item-123'
        )
        
        params = mock_invoke.call_args[1]['params']
        assert params['CallId'] == 'call-456'
        assert params['CallbackListItemId'] == 'item-123'
    
    def test_find_classifications_without_ids(self):
        """Test that find_classifications requires at least one ID."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError) as exc_info:
            client.find_classifications()
        
        assert "Either call_id or callback_list_item_id must be provided" in str(exc_info.value)
    
    @patch.object(Client, 'invoke_api')
    def test_get_call_classification_found(self, mock_invoke):
        """Test getting classification for a call that has one."""
        mock_invoke.return_value = [
            {
                'Id': 'classification-123',
                'TagSchemaName': 'Call Classification',
                'CallId': 'call-456',
                'Note': 'Test note'
            }
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_call_classification('call-456')
        
        assert result is not None
        assert result['Id'] == 'classification-123'
        assert result['CallId'] == 'call-456'
    
    @patch.object(Client, 'invoke_api')
    def test_get_call_classification_not_found(self, mock_invoke):
        """Test getting classification for a call that has none."""
        mock_invoke.return_value = []
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_call_classification('call-456')
        
        assert result is None
    
    def test_get_call_classification_empty_id(self):
        """Test that empty call_id raises ValueError."""
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        with pytest.raises(ValueError) as exc_info:
            client.get_call_classification('')
        
        assert "call_id is required" in str(exc_info.value)
    
    @patch.object(Client, 'invoke_api')
    def test_get_queue_schemas(self, mock_invoke):
        """Test retrieving queue-schema mappings."""
        mock_invoke.return_value = [
            {
                'QueueId': 'queue-1',
                'QueueName': 'Sales Queue',
                'SchemaId': 'schema-1',
                'Deleted': False
            },
            {
                'QueueId': 'queue-2',
                'QueueName': 'Support Queue',
                'SchemaId': 'schema-2',
                'Deleted': False
            }
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_queue_schemas()
        
        assert len(result) == 2
        assert result[0]['QueueId'] == 'queue-1'
        assert result[0]['QueueName'] == 'Sales Queue'
        assert result[0]['SchemaId'] == 'schema-1'
        assert result[1]['QueueId'] == 'queue-2'
        
        # Verify the API call
        call_args = mock_invoke.call_args
        assert call_args[1]['method'] == 'GET'
        assert call_args[1]['path'] == '/classification/queueschemas'
    
    @patch.object(Client, 'invoke_api')
    def test_get_calllist_schemas(self, mock_invoke):
        """Test retrieving callback list-schema mappings."""
        mock_invoke.return_value = [
            {
                'ListId': 'list-1',
                'ListName': 'Sales Callbacks',
                'SchemaId': 'schema-1',
                'RequestTypeId': 50,
                'Deleted': False
            },
            {
                'ListId': 'list-2',
                'ListName': 'Support Callbacks',
                'SchemaId': 'schema-2',
                'RequestTypeId': None,
                'Deleted': False
            }
        ]
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_calllist_schemas()
        
        assert len(result) == 2
        assert result[0]['ListId'] == 'list-1'
        assert result[0]['ListName'] == 'Sales Callbacks'
        assert result[0]['SchemaId'] == 'schema-1'
        assert result[0]['RequestTypeId'] == 50
        assert result[1]['ListId'] == 'list-2'
        assert result[1]['RequestTypeId'] is None
        
        # Verify the API call
        call_args = mock_invoke.call_args
        assert call_args[1]['method'] == 'GET'
        assert call_args[1]['path'] == '/classification/calllistschemas'
    
    @patch.object(Client, 'invoke_api')
    def test_get_call_classification_pretty(self, mock_invoke):
        """Test getting classification with pretty-printed tag names."""
        # Set up mock responses for multiple API calls
        def mock_invoke_side_effect(*args, **kwargs):
            path = kwargs.get('path', '')
            
            # First call: find_classifications
            if path == '/classification/instance/':
                return [{
                    'Id': 'classification-123',
                    'TagSchemaId': 'schema-1',
                    'CallId': 'call-123',
                    'TagSelections': [
                        {'TagId': 100},
                        {'TagId': 200},
                        {'TagId': 300},
                        {'TagId': 301}
                    ]
                }]
            
            # Second call: get_classification_schema
            elif path == '/classification/schemas/schema-1':
                return {
                    'Id': 'schema-1',
                    'Name': 'Call Classification',
                    'Groups': [
                        {
                            'Name': 'Reason for call',
                            'MaxSelections': 1,
                            'Tags': [
                                {'Id': 100, 'Name': 'Sales demo'},
                                {'Id': 101, 'Name': 'Support'}
                            ]
                        },
                        {
                            'Name': 'Customer type',
                            'MaxSelections': 1,
                            'Tags': [
                                {'Id': 200, 'Name': 'Prospect'},
                                {'Id': 201, 'Name': 'Existing'}
                            ]
                        },
                        {
                            'Name': 'Products',
                            'MaxSelections': 5,
                            'Tags': [
                                {'Id': 300, 'Name': 'Hammers'},
                                {'Id': 301, 'Name': 'Screwdrivers'},
                                {'Id': 302, 'Name': 'Drills'}
                            ]
                        }
                    ]
                }
            
            return {}
        
        mock_invoke.side_effect = mock_invoke_side_effect
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_call_classification_pretty('call-123')
        
        # Verify the classification was returned with TagsPretty
        assert result is not None
        assert 'TagsPretty' in result
        
        tags_pretty = result['TagsPretty']
        
        # Single-selection groups should be strings
        assert tags_pretty['Reason for call'] == 'Sales demo'
        assert tags_pretty['Customer type'] == 'Prospect'
        
        # Multi-selection groups should be lists
        assert isinstance(tags_pretty['Products'], list)
        assert 'Hammers' in tags_pretty['Products']
        assert 'Screwdrivers' in tags_pretty['Products']
        assert len(tags_pretty['Products']) == 2
        
        # Verify original data is still there
        assert result['Id'] == 'classification-123'
        assert result['TagSchemaId'] == 'schema-1'
        assert len(result['TagSelections']) == 4
    
    @patch.object(Client, 'invoke_api')
    def test_get_call_classification_pretty_not_found(self, mock_invoke):
        """Test pretty classification returns None when no classification exists."""
        mock_invoke.return_value = []
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        client.secretkey = 'test-key'
        client.apiEndpoint = 'https://api.test.com'
        
        result = client.get_call_classification_pretty('call-456')
        
        assert result is None

