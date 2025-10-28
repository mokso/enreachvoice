"""
Unit tests for the EnreachVoice API Client.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from enreachvoice.restapi import Client, HEADERS, DISCOVERY_URL
from enreachvoice.exceptions import (
    EnreachAPIException,
    AuthenticationException,
    RateLimitException,
)


class TestClientInit:
    """Tests for Client initialization."""
    
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.post')
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.get')
    def test_init_discovery_failure(self, mock_get):
        """Test that initialization fails when discovery fails."""
        # Mock failed discovery response
        discovery_response = Mock()
        discovery_response.status_code = 500
        discovery_response.text = "Internal Server Error"
        mock_get.return_value = discovery_response
        
        with pytest.raises(EnreachAPIException):
            Client(username='test@example.com', secretkey='test-key')


class TestGetApiUrl:
    """Tests for get_apiurl method."""
    
    @patch('enreachvoice.restapi.requests.get')
    def test_successful_discovery(self, mock_get):
        """Test successful API endpoint discovery."""
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = [{'apiEndpoint': 'https://api.test.com/'}]
        mock_get.return_value = discovery_response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        
        result = client.get_apiurl()
        
        assert result == 'https://api.test.com'
        mock_get.assert_called_once_with(f"{DISCOVERY_URL}/api/user?user=test@example.com")
    
    @patch('enreachvoice.restapi.requests.get')
    def test_discovery_removes_trailing_slash(self, mock_get):
        """Test that trailing slash is removed from API endpoint."""
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = [{'apiEndpoint': 'https://api.test.com/'}]
        mock_get.return_value = discovery_response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        
        result = client.get_apiurl()
        
        assert result == 'https://api.test.com'
    
    @patch('enreachvoice.restapi.requests.get')
    def test_discovery_error_status(self, mock_get):
        """Test discovery failure with error status."""
        discovery_response = Mock()
        discovery_response.status_code = 404
        discovery_response.text = "Not Found"
        mock_get.return_value = discovery_response
        
        client = Client.__new__(Client)
        client.username = 'test@example.com'
        
        with pytest.raises(EnreachAPIException) as exc_info:
            client.get_apiurl()
        
        assert "404" in str(exc_info.value)


class TestInvokeAPI:
    """Tests for invoke_api method."""
    
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.post')
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
    
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.post')
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
    
    @patch('enreachvoice.restapi.requests.post')
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
    
    @patch('enreachvoice.restapi.os.makedirs')
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.requests.get')
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
    
    @patch('enreachvoice.restapi.time.sleep')
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
