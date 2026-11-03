"""Tests for backend/api.py error handling enhancements.

Verifies comprehensive error handling for:
- Network errors (DNS, connection refused, timeout)
- HTTP error status codes (400-599)
- Invalid JSON responses
- User-friendly error messages
- Logging for all errors

All network calls are mocked; no actual API requests are made.
"""

import logging
from unittest import mock

import pytest
import requests

from backend import api


@pytest.fixture
def mock_logger():
    """Mock the logger to verify logging calls."""
    with mock.patch.object(api, 'logger') as mock_log:
        yield mock_log


class TestNetworkErrorHandling:
    """Test network-level error handling in _get_json."""
    
    def test_dns_resolution_failure(self, mock_logger):
        """DNS resolution failure should return user-friendly error."""
        dns_error = requests.exceptions.ConnectionError(
            "Failed to establish connection: getaddrinfo failed"
        )
        
        with mock.patch('requests.get', side_effect=dns_error):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "DNS resolution failed"
        assert "DNS settings" in result["detail"]
        mock_logger.error.assert_called_once()
        assert "DNS resolution failed" in mock_logger.error.call_args[0][0]
    
    def test_connection_refused(self, mock_logger):
        """Connection refused should return user-friendly error."""
        refused_error = requests.exceptions.ConnectionError(
            "Connection refused by server"
        )
        
        with mock.patch('requests.get', side_effect=refused_error):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Connection refused"
        assert "server refused" in result["detail"]
        mock_logger.error.assert_called_once()
    
    def test_generic_connection_error(self, mock_logger):
        """Generic connection errors should return network error message."""
        conn_error = requests.exceptions.ConnectionError(
            "Network unreachable"
        )
        
        with mock.patch('requests.get', side_effect=conn_error):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "No network connection"
        assert "graphhopper.com" in result["detail"]
        mock_logger.error.assert_called_once()
    
    def test_timeout_error(self, mock_logger):
        """Timeout errors should return timeout message."""
        timeout_error = requests.exceptions.Timeout("Request timed out")
        
        with mock.patch('requests.get', side_effect=timeout_error):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "The request timed out"
        assert "10 seconds" in result["detail"]
        mock_logger.error.assert_called_once()
    
    def test_generic_request_exception(self, mock_logger):
        """Other request exceptions should be caught gracefully."""
        generic_error = requests.exceptions.RequestException(
            "Unknown network error"
        )
        
        with mock.patch('requests.get', side_effect=generic_error):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Network request failed"
        assert "RequestException" in result["detail"]
        mock_logger.error.assert_called_once()


class TestHTTPErrorHandling:
    """Test HTTP status code error handling."""
    
    def test_401_unauthorized(self, mock_logger):
        """HTTP 401 should return API key error."""
        mock_response = mock.Mock()
        mock_response.status_code = 401
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Invalid or unauthorized API key"
        assert "API rejected the key" in result["detail"]
        mock_logger.warning.assert_called_once()
    
    def test_403_forbidden(self, mock_logger):
        """HTTP 403 should return API key error."""
        mock_response = mock.Mock()
        mock_response.status_code = 403
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Invalid or unauthorized API key"
        mock_logger.warning.assert_called_once()
    
    def test_400_bad_request(self, mock_logger):
        """HTTP 400 should return client error."""
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Client error (400)"
        assert "400" in result["detail"]
        assert "Bad Request" in result["detail"]
        mock_logger.error.assert_called_once()
    
    def test_404_not_found(self, mock_logger):
        """HTTP 404 should return client error."""
        mock_response = mock.Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Client error (404)"
        mock_logger.error.assert_called_once()

    def test_429_rate_limit(self, mock_logger):
        """HTTP 429 should explain that the API is throttling requests."""
        mock_response = mock.Mock()
        mock_response.status_code = 429

        with mock.patch("requests.get", return_value=mock_response):
            result = api._get_json("https://example.com")

        assert result["ok"] is False
        assert result["title"] == "API rate limit reached"
        assert "wait" in result["detail"].lower()
        mock_logger.warning.assert_called_once()
    
    def test_500_server_error(self, mock_logger):
        """HTTP 500 should return server error."""
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Server error (500)"
        assert "500" in result["detail"]
        assert "Internal Server Error" in result["detail"]
        mock_logger.error.assert_called_once()
    
    def test_503_service_unavailable(self, mock_logger):
        """HTTP 503 should return server error."""
        mock_response = mock.Mock()
        mock_response.status_code = 503
        mock_response.reason = "Service Unavailable"
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Server error (503)"
        mock_logger.error.assert_called_once()


class TestJSONParsingErrorHandling:
    """Test JSON parsing error handling."""
    
    def test_invalid_json_response(self, mock_logger):
        """Invalid JSON should return parsing error."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Not valid JSON content"
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Unexpected response from the API"
        assert "not valid JSON" in result["detail"]
        mock_logger.error.assert_called_once()
        # Verify it logs the invalid content
        log_call = mock_logger.error.call_args[0][0]
        assert "Invalid JSON" in log_call
    
    def test_unexpected_json_parsing_exception(self, mock_logger):
        """Unexpected exceptions during JSON parsing should be caught."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = RuntimeError("Unexpected error")
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["ok"] is False
        assert result["title"] == "Failed to process API response"
        assert "RuntimeError" in result["detail"]
        mock_logger.error.assert_called_once()


class TestSuccessfulResponse:
    """Test successful response handling."""
    
    def test_valid_json_response(self, mock_logger):
        """Valid JSON response should be returned."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": [1, 2, 3]}
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert result["status"] == "success"
        assert result["data"] == [1, 2, 3]
        mock_logger.debug.assert_called_once()


class TestGeocodeErrorHandling:
    """Test error handling in geocode function."""
    
    def test_geocode_logs_query(self, mock_logger):
        """Geocode should log the query."""
        mock_result = {"ok": False, "title": "Error", "detail": "Details"}
        
        with mock.patch.object(api, '_get_json', return_value=mock_result):
            api.geocode("test-key", "Test Location")
        
        # Check that geocode logged the query
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Test Location" in call for call in info_calls)
    
    def test_geocode_logs_network_failures(self, mock_logger):
        """Network failures should be logged."""
        network_error = {"ok": False, "title": "No network", "detail": "Details"}
        
        with mock.patch.object(api, '_get_json', return_value=network_error):
            result = api.geocode("test-key", "Manila")
        
        assert result["ok"] is False
        mock_logger.warning.assert_called()
        assert "No network" in mock_logger.warning.call_args[0][0]
    
    def test_geocode_logs_no_results(self, mock_logger):
        """No geocoding results should be logged."""
        with mock.patch.object(api, '_get_json', return_value={"hits": []}):
            result = api.geocode("test-key", "InvalidPlace12345")
        
        assert result["ok"] is False
        assert "Location not found" in result["title"]
        mock_logger.warning.assert_called()
    
    def test_geocode_logs_api_error_message(self, mock_logger):
        """API error messages should be logged."""
        error_response = {"message": "API quota exceeded", "hits": []}
        
        with mock.patch.object(api, '_get_json', return_value=error_response):
            result = api.geocode("test-key", "Manila")
        
        assert result["ok"] is False
        mock_logger.error.assert_called()
        assert "API quota exceeded" in mock_logger.error.call_args[0][0]
    
    def test_geocode_logs_success(self, mock_logger):
        """Successful geocoding should be logged."""
        success_response = {
            "hits": [{
                "name": "Manila",
                "city": "Manila",
                "country": "Philippines",
                "point": {"lat": 14.5995, "lng": 120.9842}
            }]
        }
        
        with mock.patch.object(api, '_get_json', return_value=success_response):
            result = api.geocode("test-key", "Manila")
        
        assert result["ok"] is True
        # Check for success log
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Successfully geocoded" in call for call in info_calls)


class TestFetchRouteErrorHandling:
    """Test error handling in fetch_route function."""
    
    def test_fetch_route_logs_request(self, mock_logger):
        """fetch_route should log the request details."""
        with mock.patch.object(api, 'geocode', return_value={
            "ok": False, "title": "Error", "detail": "Details"
        }):
            api.fetch_route("key", "A", "B", "metric", "car")
        
        # Check that it logged the request
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Fetching route" in call and "metric" in call and "car" in call 
                   for call in info_calls)
    
    def test_fetch_route_logs_geocoding_failure(self, mock_logger):
        """Geocoding failures should be logged."""
        geocode_error = {"ok": False, "title": "Location not found", "detail": "Details"}
        
        with mock.patch.object(api, 'geocode', return_value=geocode_error):
            result = api.fetch_route("key", "InvalidPlace", "Manila", "metric", "car")
        
        assert result["ok"] is False
        mock_logger.error.assert_called()
        error_log = mock_logger.error.call_args[0][0]
        assert "geocoding failed" in error_log
    
    def test_fetch_route_logs_routing_api_error(self, mock_logger):
        """Routing API errors should be logged."""
        geocode_success = {
            "ok": True,
            "name": "Manila",
            "point": {"lat": 14.5995, "lng": 120.9842}
        }
        route_error = {"message": "No route found", "paths": None}
        
        with mock.patch.object(api, 'geocode', return_value=geocode_success):
            with mock.patch.object(api, '_get_json', return_value=route_error):
                result = api.fetch_route("key", "A", "B", "metric", "car")
        
        assert result["ok"] is False
        mock_logger.error.assert_called()
        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("No route found" in call for call in error_calls)
    
    def test_fetch_route_logs_missing_paths(self, mock_logger):
        """Missing paths in response should be logged."""
        geocode_success = {
            "ok": True,
            "name": "Manila",
            "point": {"lat": 14.5995, "lng": 120.9842}
        }
        invalid_response = {"status": "ok"}  # Missing 'paths'
        
        with mock.patch.object(api, 'geocode', return_value=geocode_success):
            with mock.patch.object(api, '_get_json', return_value=invalid_response):
                result = api.fetch_route("key", "A", "B", "metric", "car")
        
        assert result["ok"] is False
        assert "unexpected" in result["detail"].lower()
        mock_logger.error.assert_called()
    
    def test_fetch_route_logs_success(self, mock_logger):
        """Successful route fetch should be logged."""
        geocode_success = {
            "ok": True,
            "name": "Manila",
            "point": {"lat": 14.5995, "lng": 120.9842}
        }
        route_success = {
            "paths": [{
                "distance": 15830,
                "time": 1800000,
                "instructions": [],
                "points": {"coordinates": [[120.98, 14.59], [121.00, 14.60]]}
            }]
        }
        
        with mock.patch.object(api, 'geocode', return_value=geocode_success):
            with mock.patch.object(api, '_get_json', return_value=route_success):
                result = api.fetch_route("key", "A", "B", "metric", "car")
        
        assert result["ok"] is True
        # Check for success log
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Successfully fetched route" in call for call in info_calls)


class TestUserFriendlyErrorMessages:
    """Test that all error messages are user-friendly."""
    
    def test_no_technical_jargon_in_connection_errors(self):
        """Connection error messages should be non-technical."""
        conn_error = requests.exceptions.ConnectionError("socket error")
        
        with mock.patch('requests.get', side_effect=conn_error):
            result = api._get_json("https://example.com")
        
        # Should not contain technical terms like "socket", "TCP", etc.
        assert "socket" not in result["detail"].lower()
        # Should contain helpful guidance
        assert "internet" in result["detail"].lower() or "connection" in result["detail"].lower()
    
    def test_timeout_messages_are_actionable(self):
        """Timeout messages should suggest retry."""
        timeout_error = requests.exceptions.Timeout()
        
        with mock.patch('requests.get', side_effect=timeout_error):
            result = api._get_json("https://example.com")
        
        assert "try again" in result["detail"].lower()
        assert str(api.TIMEOUT_SECONDS) in result["detail"]
    
    def test_auth_errors_provide_resolution_steps(self):
        """Auth error messages should guide user to fix API key."""
        mock_response = mock.Mock()
        mock_response.status_code = 401
        
        with mock.patch('requests.get', return_value=mock_response):
            result = api._get_json("https://example.com")
        
        assert "graphhopper.com" in result["detail"].lower()
        assert "config.ini" in result["detail"].lower() or "key" in result["detail"].lower()
