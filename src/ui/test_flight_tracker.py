import pytest
from unittest.mock import Mock, patch
import requests
import time
from queue import Queue
from dataclasses import dataclass

# Import the necessary classes and functions from your main file
from app import (
    send_flight_data_to_nifi,
    get_time_to_arrival,
    poll_arrival_time,
    FlightData,
    Config
)

# Mock flight data for testing
@dataclass
class MockFlight:
    icao24: str = "407c89"
    lastSeen: int = int(time.time())
    callsign: str = "TEST123"
    estArrivalAirport: str = "EGLL"

@pytest.fixture
def mock_flight():
    return MockFlight()

@pytest.fixture
def mock_flight_data():
    return FlightData(
        icao24="abc123",
        timestamp=int(time.time()),
        host_id="test-host-id",
        session_id="test-session-id",
        lastSeen=int(time.time()),
        callSign="TEST123",
        arrivalAirport="EGLL"
    )

class TestNiFiIntegration:
    
    @pytest.mark.integration
    def test_send_flight_data_to_nifi_success(self, mock_flight):
        """Test successful sending of flight data to NiFi"""
        with patch('requests.post') as mock_post:
            # Configure the mock to return a successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            success, error = send_flight_data_to_nifi(
                mock_flight,
                "test-host-id",
                "test-session-id",
                int(time.time()),
                Config.NIFI_ENDPOINT
            )

            assert success is True
            assert error is None
            mock_post.assert_called_once()
            
            # Verify the correct headers were sent
            called_headers = mock_post.call_args.kwargs['headers']
            assert called_headers['Content-Type'] == 'application/json'
            assert called_headers['X-Host-ID'] == "test-host-id"
            assert called_headers['X-Session-ID'] == "test-session-id"

    @pytest.mark.integration
    def test_send_flight_data_to_nifi_failure(self, mock_flight):
        """Test handling of NiFi connection failure"""
        with patch('requests.post') as mock_post:
            # Configure the mock to raise an exception
            mock_post.side_effect = requests.exceptions.RequestException("Connection failed")

            success, error = send_flight_data_to_nifi(
                mock_flight,
                "test-host-id",
                "test-session-id",
                int(time.time()),
                Config.NIFI_ENDPOINT
            )

            assert success is False
            assert "Connection failed" in error
            mock_post.assert_called_once()

    @pytest.mark.integration
    def test_get_time_to_arrival_success(self):
        """Test successful retrieval of arrival time from NiFi"""
        expected_data = {"time_to_arrival": "3600"}  # 1 hour in seconds
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_data
            mock_get.return_value = mock_response

            result = get_time_to_arrival("test-session-id")

            assert result == expected_data
            mock_get.assert_called_once_with(
                Config.NIFI_GET_ENDPOINT,
                headers={'X-Session-ID': 'test-session-id'},
                timeout=5
            )

    @pytest.mark.integration
    def test_get_time_to_arrival_failure(self):
        """Test handling of failed arrival time retrieval"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

            result = get_time_to_arrival("test-session-id")

            assert result == {"time_to_arrival": "null"}
            mock_get.assert_called_once()

    @pytest.mark.integration
    def test_poll_arrival_time_success(self):
        """Test successful polling of arrival time"""
        expected_data = {"time_to_arrival": "3600"}
        
        with patch('your_module.get_time_to_arrival') as mock_get:
            # Return null a few times before returning the actual data
            mock_get.side_effect = [
                {"time_to_arrival": "null"},
                {"time_to_arrival": "null"},
                expected_data
            ]

            result_queue = Queue()
            poll_arrival_time("test-session-id", result_queue)
            result = result_queue.get(timeout=1)

            assert result == expected_data

    @pytest.mark.integration
    def test_poll_arrival_time_timeout(self):
        """Test handling of polling timeout"""
        with patch('your_module.get_time_to_arrival') as mock_get:
            # Always return null to trigger timeout
            mock_get.return_value = {"time_to_arrival": "null"}

            result_queue = Queue()
            poll_arrival_time("test-session-id", result_queue)
            result = result_queue.get(timeout=1)

            assert "error" in result
            assert "Sorry we couldn't retrieve the data" in result["error"]

    @pytest.mark.integration
    def test_end_to_end_flight_data_flow(self, mock_flight):
        """Test the complete flow of sending data and receiving arrival time"""
        with patch('requests.post') as mock_post, \
             patch('your_module.get_time_to_arrival') as mock_get:
            
            # Mock successful data sending
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post.return_value = mock_post_response

            # Mock successful arrival time retrieval
            mock_get.return_value = {"time_to_arrival": "3600"}

            # Send flight data
            success, error = send_flight_data_to_nifi(
                mock_flight,
                "test-host-id",
                "test-session-id",
                int(time.time()),
                Config.NIFI_ENDPOINT
            )

            assert success is True
            assert error is None

            # Get arrival time
            result_queue = Queue()
            poll_arrival_time("test-session-id", result_queue)
            result = result_queue.get(timeout=1)

            assert result["time_to_arrival"] == "3600"