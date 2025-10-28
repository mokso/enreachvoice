import os
import requests
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union, cast
import time

from .exceptions import (
    EnreachAPIException,
    AuthenticationException,
    RateLimitException,
)

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Json-Serializer': '2',
    'User-Agent': 'enreachvoice-python/0.1',
}
DISCOVERY_URL = 'https://discover.enreachvoice.com'

class Client:
    """
    EnreachVoice API Client.
    
    This client provides access to the EnreachVoice REST API for managing
    calls, users, queues, and other telephony resources.
    
    Args:
        username: User email address
        secretkey: API secret key (optional if password provided)
        password: User password (optional if secretkey provided)
        
    Raises:
        EnreachAPIException: If service discovery fails
        AuthenticationException: If authentication fails
        ValueError: If neither secretkey nor password is provided
        
    Example:
        >>> client = Client(username='user@example.com', secretkey='your-secret-key')
        >>> calls = client.get_usercalls(StartTime=start, EndTime=end)
    """
    
    def __init__(
        self, 
        username: str, 
        secretkey: Optional[str] = None, 
        password: Optional[str] = None
    ):
        self.username = username
        self.apiEndpoint = self.get_apiurl()
        self.userid: Optional[str] = None
        self.secretkey: Optional[str] = None

        if secretkey is not None:
            logging.debug("Using provided secretkey")
            self.secretkey = secretkey
        else:
            logging.debug("No secretkey provided")
            if password is None:
                raise ValueError("Either secretkey or password must be provided")
            logging.debug("Got password, using that to retrieve secretkey")
            self.secretkey = self.authenticate_with_password(password)

        user = self.invoke_api(method='GET', path='users/me')
        self.userid = user['Id']

    def get_apiurl(self) -> str:
        """
        Invoke discovery service to get the API endpoint.
        https://doc.enreachvoice.com/beneapi/#service-discovery

        Returns:
            API endpoint URL
            
        Raises:
            EnreachAPIException: If discovery fails
        """
        try:
            url = f"{DISCOVERY_URL}/api/user?user={self.username}"
            logging.debug(f"Invoking discovery: {url}")
            discoveryResponse = requests.get(url)
            if discoveryResponse.status_code != 200:
                logging.error(f"Discovery failed: {discoveryResponse.status_code} {discoveryResponse.text}")
                raise EnreachAPIException(
                    f"Discovery failed with status {discoveryResponse.status_code}",
                    status_code=discoveryResponse.status_code,
                    response=discoveryResponse.text
                )
            logging.debug(f"Discovery response: {json.dumps(discoveryResponse.json(),indent=2)}")
            apiEndpoint: str = discoveryResponse.json()[0]['apiEndpoint']
            # if api url has ending slash, remove it
            if apiEndpoint[-1] == '/':
                apiEndpoint = apiEndpoint[:-1]
            logging.info(f"API endpoint: {apiEndpoint}")
            return apiEndpoint
        except requests.RequestException as e:
            logging.error(f"Network error invoking discovery: {e}")
            raise EnreachAPIException(f"Network error during discovery: {e}")
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f"Invalid discovery response: {e}")
            raise EnreachAPIException(f"Invalid discovery response: {e}")
        except EnreachAPIException:
            raise
        except Exception as e:
            logging.error(f"Error invoking discovery: {e}")
            raise EnreachAPIException(f"Unexpected error during discovery: {e}")

    def invoke_api(
        self, 
        path: str, 
        method: str = 'GET', 
        params: Optional[Dict[str, Any]] = None, 
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke the EnreachVoice API with the given method, path, parameters and payload.

        Args:
            path: Path to the API endpoint
            method: HTTP method to use. Default is 'GET'
            params: Query parameters to send with the request
            payload: Payload to send with the request

        Returns:
            API response as dictionary
            
        Raises:
            ValueError: If method or path is invalid
            EnreachAPIException: If API request fails
        """
        # ensure we have a valid method
        if method not in ['GET', 'POST', 'PUT', 'DELETE']:
            raise ValueError(f"Invalid method: {method}. Must be GET, POST, PUT, or DELETE")
        
        # ensure we have a valid path
        if path is None:
            raise ValueError("Path must be provided")
        
        #ensure path starts with a slash
        if path[0] != '/':
            path = '/' + path

        url = f"{self.apiEndpoint}{path}"
        logging.debug(f"Invoking {method}: {url}")
        
        try:
            start_time = time.time()
            if method == 'GET':
                response = requests.get(url, headers=HEADERS, auth=(self.username, cast(str, self.secretkey)), params=params)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, auth=(self.username, cast(str, self.secretkey)), params=params, data=(json.dumps(payload)))
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, auth=(self.username, cast(str, self.secretkey)), params=params, data=(json.dumps(payload)))
            elif method == 'DELETE':
                response = requests.delete(url, headers=HEADERS, auth=(self.username, cast(str, self.secretkey)), params=params)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Try to parse JSON response
            try:
                json_response: Dict[str, Any] = response.json()
                logging.debug(f"Got response {response.status_code} in {duration_ms:.2f} ms: {json.dumps(json_response, indent=2)}")
            except ValueError as e:
                logging.error(f"Invalid JSON response: {response.text}")
                raise EnreachAPIException(
                    f"API returned invalid JSON: {str(e)}",
                    status_code=response.status_code,
                    response=response.text
                )
            
            # Check response status
            if response.status_code == 401:
                raise AuthenticationException(
                    "Authentication failed. Check your credentials.",
                    status_code=response.status_code,
                    response=json_response
                )
            elif response.status_code == 404:
                raise EnreachAPIException(
                    f"Resource not found: {path}",
                    status_code=response.status_code,
                    response=json_response
                )
            elif response.status_code == 429:
                raise RateLimitException(
                    "API rate limit exceeded. Please retry later.",
                    status_code=response.status_code,
                    response=json_response
                )
            elif not response.ok:
                raise EnreachAPIException(
                    f"API request failed: {response.status_code}",
                    status_code=response.status_code,
                    response=json_response
                )
            
            return json_response
            
        except (AuthenticationException, RateLimitException, EnreachAPIException):
            raise
        except requests.RequestException as e:
            logging.error(f"Network error while invoking REST API: {e}")
            raise EnreachAPIException(f"Network error: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error while invoking REST API: {e}")
            raise EnreachAPIException(f"Unexpected error: {str(e)}")

    def authenticate_with_password(self, password: str) -> str:
        """
        Authenticate with the EnreachVoice API using the provided user password.
        https://doc.enreachvoice.com/beneapi/#post-authuser-email

        Args:
            password: User password

        Returns:
            Secret key for API authentication
            
        Raises:
            AuthenticationException: If authentication fails
        """
        try:
            url = f"{self.apiEndpoint}/authuser/{self.username}"
            payload = {
                'UserName': self.username,
                'Password': password,
            }
            logging.debug(f"Invoking POST: {url}")
            response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
            if response.status_code != 200:
                logging.error(f"Authentication failed: {response.status_code} {response.text}")
                raise AuthenticationException(
                    f"Authentication failed with status {response.status_code}",
                    status_code=response.status_code,
                    response=response.text
                )
                        
            logging.debug(f"API response: {json.dumps(response.json(),indent=2)}")
            secretkey: str = response.json()['SecretKey']
            logging.info(f"User {self.username} authenticated successfully")
            return secretkey
        except AuthenticationException:
            raise
        except requests.RequestException as e:
            logging.error(f"Network error during authentication: {e}")
            raise AuthenticationException(f"Network error during authentication: {e}")
        except (KeyError, ValueError) as e:
            logging.error(f"Invalid authentication response: {e}")
            raise AuthenticationException(f"Invalid authentication response: {e}")
        except Exception as e:
            logging.error(f"Error authenticating: {e}")
            raise AuthenticationException(f"Unexpected error during authentication: {e}")
               
    def get_usercalls(self, **filterParameters: Any) -> List[Dict[str, Any]]:
        """
        Get user call events. That is, call events that are associated to a user. The same callId can be
        associated to multiple call events.

        https://doc.enreachvoice.com/beneapi/#get-calls

        Args:
            **filterParameters: Filter parameters to apply to the call events query
                https://doc.enreachvoice.com/beneapi/#callfilterparameters
                Give 'DateTime' as datetime objects, they will be converted to proper string format
        
        Returns:
            List of user calls
            
        Raises:
            ValueError: If filter parameters are invalid
            EnreachAPIException: If API request fails
        """
        logging.debug(f"Filter parameters: {json.dumps(filterParameters,indent=2,default=str)}")
        # Ensure we have either StartTime and EndTime, ModifiedAfter and ModifiedBefore, or CallId
        # Time range cannot be more than 31 days
        # Times must be given in proper string format in UTC, like "2015-01-01 06:00:00"

        if 'StartTime' in filterParameters and 'EndTime' in filterParameters:
            st = filterParameters['StartTime']
            filterParameters['StartTime'] = st.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            et = filterParameters['EndTime']
            filterParameters['EndTime'] = et.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            if (et - st).days > 31:
                raise ValueError("Time range cannot be more than 31 days")
        elif 'ModifiedAfter' in filterParameters and 'ModifiedBefore' in filterParameters:
            ma = filterParameters['ModifiedAfter']
            filterParameters['ModifiedAfter'] = ma.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            mb = filterParameters['ModifiedBefore']
            filterParameters['ModifiedBefore'] = mb.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            if (mb - ma).days > 31:
                raise ValueError("Time range cannot be more than 31 days")
        elif 'CallId' in filterParameters:
            pass
        else:
            raise ValueError("Must have StartTime and EndTime or ModifiedAfter and ModifiedBefore")
        
        calls_response = self.invoke_api(method='GET', path='/calls', params=filterParameters)
        calls = cast(List[Dict[str, Any]], calls_response)
        
        logging.info(f"Retrieved {len(calls)} calls")
        return calls

    def get_inbound_queuecalls(self, **filterParameters: Any) -> List[Dict[str, Any]]:
        """
        Get inbound queuecalls aka. servicecalls.
        https://doc.enreachvoice.com/beneapi/#get-servicecall

        Args:
            **filterParameters: Filter parameters to apply to the servicecall query
                https://doc.enreachvoice.com/beneapi/#servicecallfilterparameters
                Give 'DateTime' as datetime objects, they will be converted to proper string format
        
        Returns:
            List of service calls
            
        Raises:
            ValueError: If filter parameters are invalid
            EnreachAPIException: If API request fails
        """
        logging.debug(f"Filter parameters: {json.dumps(filterParameters,indent=2,default=str)}")
        # Ensure we have either StartTime and EndTime, or ModifiedAfter and ModifiedBefore
        # Time range cannot be more than 31 days
        # Times must be given in proper string format in UTC, like "2015-01-01 06:00:00"

        if 'StartTime' in filterParameters and 'EndTime' in filterParameters:
            st = filterParameters['StartTime']
            filterParameters['StartTime'] = st.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            et = filterParameters['EndTime']
            filterParameters['EndTime'] = et.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            if (et - st).days > 31:
                raise ValueError("Time range cannot be more than 31 days")
        elif 'ModifiedAfter' in filterParameters and 'ModifiedBefore' in filterParameters:
            ma = filterParameters['ModifiedAfter']
            filterParameters['ModifiedAfter'] = ma.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            mb = filterParameters['ModifiedBefore']
            filterParameters['ModifiedBefore'] = mb.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            if (mb - ma).days > 31:
                raise ValueError("Time range cannot be more than 31 days")
        else:
            raise ValueError("Must have StartTime and EndTime or ModifiedAfter and ModifiedBefore")
        
        calls = self.invoke_api(method='GET', path='/servicecall', params=filterParameters)
        logging.info(f"Retrieved {len(calls)} service calls")
        return cast(List[Dict[str, Any]], calls)


    def get_recording_file(self, recordingId: str, path: str) -> None:
        """
        Download recording to mp3-file.
        https://doc.enreachvoice.com/beneapi/#get-calls-recordings-recordingid

        Args:
            recordingId: RecordingId of the recording to get
            path: Path directory to save the recording file. File will be saved as <recordingId>.mp3
            
        Raises:
            EnreachAPIException: If recording download fails
        """
        # ensure path exists
        os.makedirs(path, exist_ok=True)

        url = f"{self.apiEndpoint}/calls/recordings/{recordingId}"
        logging.debug(f"Invoking GET: {url}")
        recording_response = requests.get(url, headers=HEADERS, auth=(self.username, cast(str, self.secretkey)))
        if recording_response.status_code != 200:
            logging.error(f"Get recording failed: {recording_response.status_code} {recording_response.text}")
            raise EnreachAPIException(
                f"Failed to get recording metadata: {recording_response.status_code}",
                status_code=recording_response.status_code,
                response=recording_response.text
            )
        recording_metadata = recording_response.json()
        logging.info(f"Retrieved recording metadata: {json.dumps(recording_metadata,indent=2)}")
        recordingUrl = f"{self.apiEndpoint}/{recording_metadata['URL']}"
        logging.debug(f"Invoking GET: {recordingUrl}")
        recording_audio = requests.get(recordingUrl)    

        with open(f"{path}/{recordingId}.mp3", 'wb') as f:
            f.write(recording_audio.content)
        logging.info(f"Recording file saved to {path}/{recordingId}.mp3")


    def get_transcript(self, transcriptId: str, wait_pending: bool = True) -> Dict[str, Any]:
        """
        Get transcript by transcriptId.

        Args:
            transcriptId: TranscriptId of the transcript to get
            wait_pending: If True, wait for pending transcript to be ready. Default is True

        Returns:
            Transcript data
            
        Raises:
            EnreachAPIException: If transcript retrieval fails
        """
        # GET /calls/transcripts/{transcriptId}
        path = f"/calls/transcripts/{transcriptId}"
        transcript = self.invoke_api(method='GET', path=path)
        
        # check status, if pending, wait for it to be ready
        status = transcript['TranscriptStatus']
        if status == 'Pending' and wait_pending:
            max_retries = 10
            retries = 0
            while status == 'Pending':
                if retries >= max_retries:
                    raise EnreachAPIException(f"Transcript {transcriptId} still pending after {max_retries} retries")
                
                retries += 1
                time.sleep(10)
                transcript = self.invoke_api(method='GET', path=path)
                status = transcript['TranscriptStatus']
                logging.info(f"Retrieved transcript status: {status}")
        
        return transcript

            
                




 