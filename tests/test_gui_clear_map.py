"""Integration tests for RouteApp._on_clear() with map widget reset.

Tests verify that the Clear button properly resets the map widget along
with other UI elements, and that errors are handled gracefully.

**Validates: Requirements 10.6, User requirement 2 (error handling)**
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, MagicMock, patch
from src.frontend.desktop.gui import RouteApp


class TestRouteAppClearWithMap:
    """Test suite for RouteApp._on_clear() map reset functionality."""
    
    @pytest.fixture
    def root(self):
        """Create a tkinter root window."""
        root = tk.Tk()
        yield root
        # Clean up
        try:
            root.destroy()
        except tk.TclError:
            pass
    
    @pytest.fixture
    def app_with_map(self, root):
        """Create RouteApp with mocked MapWidget."""
        with patch('src.frontend.desktop.gui.MAP_WIDGET_AVAILABLE', True):
            with patch('src.frontend.desktop.gui.MapWidget') as MockMapWidget:
                mock_map = MagicMock()
                MockMapWidget.return_value = mock_map
                
                app = RouteApp(root)
                
                yield app, mock_map
    
    @pytest.fixture
    def app_without_map(self, root):
        """Create RouteApp without MapWidget."""
        with patch('src.frontend.desktop.gui.MAP_WIDGET_AVAILABLE', False):
            app = RouteApp(root)
            yield app
    
    def test_on_clear_resets_map_widget(self, app_with_map):
        """Test that _on_clear calls reset_view on map widget.
        
        Validates: Requirement 10.6
        """
        app, mock_map = app_with_map
        
        # Set some values in the UI
        app.origin_var.set("Portland")
        app.destination_var.set("Seattle")
        app.units_var.set("metric")
        app.profile_var.set("bike")
        
        # Call _on_clear
        app._on_clear()
        
        # Verify map widget reset was called
        mock_map.reset_view.assert_called_once()
    
    def test_on_clear_resets_all_ui_elements(self, app_with_map):
        """Test that _on_clear resets all UI elements along with map.
        
        Validates: Requirement 10.6
        """
        app, mock_map = app_with_map
        
        # Set some values
        app.origin_var.set("Portland")
        app.destination_var.set("Seattle")
        app.units_var.set("metric")
        app.profile_var.set("bike")
        app.result_text.configure(state="normal")
        app.result_text.insert("end", "Some route data")
        app.result_text.configure(state="disabled")
        
        # Call _on_clear
        app._on_clear()
        
        # Verify all UI elements reset
        assert app.origin_var.get() == ""
        assert app.destination_var.get() == ""
        assert app.units_var.get() == "imperial"
        assert app.profile_var.get() == "car"
        assert app.result_text.get("1.0", "end").strip() == ""
        assert app.status_var.get() == "Enter a starting location and a destination."
        
        # Verify map reset was called
        mock_map.reset_view.assert_called_once()
    
    def test_on_clear_handles_map_reset_error_gracefully(self, app_with_map):
        """Test that _on_clear continues clearing UI even if map reset fails.
        
        Validates: User requirement 2 (error handling)
        """
        app, mock_map = app_with_map
        
        # Make reset_view raise an exception
        mock_map.reset_view.side_effect = Exception("Map reset failed")
        
        # Set some values
        app.origin_var.set("Portland")
        app.destination_var.set("Seattle")
        
        # Call _on_clear - should not raise exception
        app._on_clear()
        
        # Verify UI elements were still cleared despite map error
        assert app.origin_var.get() == ""
        assert app.destination_var.get() == ""
        assert app.units_var.get() == "imperial"
        assert app.profile_var.get() == "car"
        assert app.status_var.get() == "Enter a starting location and a destination."
    
    def test_on_clear_handles_none_map_widget(self, app_without_map):
        """Test that _on_clear handles None map widget gracefully.
        
        Validates: User requirement 2 (error handling)
        """
        app = app_without_map
        
        # Verify map_widget is None (not available)
        assert app.map_widget is None
        
        # Set some values
        app.origin_var.set("Portland")
        app.destination_var.set("Seattle")
        
        # Call _on_clear - should not raise exception
        app._on_clear()
        
        # Verify UI elements were cleared
        assert app.origin_var.get() == ""
        assert app.destination_var.get() == ""
        assert app.units_var.get() == "imperial"
        assert app.profile_var.get() == "car"
    
    def test_on_clear_logs_map_reset_error(self, app_with_map):
        """Test that _on_clear logs errors from map reset.
        
        Validates: User requirement 2 (error handling)
        """
        app, mock_map = app_with_map
        
        # Make reset_view raise a specific exception
        mock_map.reset_view.side_effect = RuntimeError("Connection lost")
        
        # Mock the logger to verify logging
        with patch('src.frontend.desktop.gui.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Call _on_clear
            app._on_clear()
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args
            assert "Failed to reset map view" in error_call[0][0]
            assert "RuntimeError: Connection lost" in error_call[0][0]
            assert error_call[1]['exc_info'] is True
    
    def test_on_clear_does_not_call_reset_on_none_widget(self, app_with_map):
        """Test that _on_clear does not call reset_view if map_widget is None.
        
        Validates: User requirement 2 (defensive programming)
        """
        app, mock_map = app_with_map
        
        # Set map_widget to None (simulating initialization failure)
        app.map_widget = None
        
        # Call _on_clear - should not raise exception or attempt to call reset
        app._on_clear()
        
        # Verify reset_view was not called
        mock_map.reset_view.assert_not_called()
    
    def test_on_clear_execution_order(self, app_with_map):
        """Test that _on_clear clears UI elements before attempting map reset.
        
        This ensures UI clearing happens even if map reset raises early.
        Validates: User requirement 2 (error handling priority)
        """
        app, mock_map = app_with_map
        
        # Set some values
        app.origin_var.set("Portland")
        app.destination_var.set("Seattle")
        
        # Make map reset fail early
        mock_map.reset_view.side_effect = Exception("Early failure")
        
        # Call _on_clear
        app._on_clear()
        
        # Verify UI was cleared before map reset attempt
        assert app.origin_var.get() == ""
        assert app.destination_var.get() == ""
        
        # Verify map reset was attempted
        mock_map.reset_view.assert_called_once()


class TestRouteAppTimeoutHandling:
    """Test suite for timeout handling with map clearing."""
    
    @pytest.fixture
    def root(self):
        """Create a tkinter root window."""
        root = tk.Tk()
        yield root
        # Clean up
        try:
            root.destroy()
        except tk.TclError:
            pass
    
    @pytest.fixture
    def app_with_map(self, root):
        """Create RouteApp with mocked MapWidget."""
        with patch('src.frontend.desktop.gui.MAP_WIDGET_AVAILABLE', True):
            with patch('src.frontend.desktop.gui.MapWidget') as MockMapWidget:
                mock_map = MagicMock()
                MockMapWidget.return_value = mock_map
                
                app = RouteApp(root)
                
                yield app, mock_map
    
    def test_timeout_result_clears_map(self, app_with_map):
        """Test that timeout result clears the map widget.
        
        Validates: Requirements 10.3, 15.6
        """
        app, mock_map = app_with_map
        
        # Create a timeout result
        timeout_result = {
            "ok": False,
            "title": "The request timed out",
            "detail": "The route request did not complete within 30 seconds."
        }
        
        # Simulate _on_result being called with timeout
        app._on_result(timeout_result)
        
        # Verify map was cleared
        mock_map.clear_route.assert_called_once()
    
    def test_timeout_result_shows_error_in_status(self, app_with_map):
        """Test that timeout result shows error message in status bar.
        
        Validates: Requirement 15.6
        """
        app, mock_map = app_with_map
        
        # Create a timeout result
        timeout_result = {
            "ok": False,
            "title": "The request timed out",
            "detail": "The route request did not complete within 30 seconds."
        }
        
        # Simulate _on_result being called with timeout
        app._on_result(timeout_result)
        
        # Verify status bar shows timeout message
        assert app.status_var.get() == "The request timed out"
    
    def test_timeout_result_re_enables_button(self, app_with_map):
        """Test that timeout result re-enables the search button.
        
        Validates: Requirement 15.6
        """
        app, mock_map = app_with_map
        
        # Disable the button (as _on_search does)
        app.search_button.configure(state="disabled")
        
        # Create a timeout result
        timeout_result = {
            "ok": False,
            "title": "The request timed out",
            "detail": "The route request did not complete within 30 seconds."
        }
        
        # Simulate _on_result being called with timeout
        app._on_result(timeout_result)
        
        # Verify button was re-enabled
        assert str(app.search_button["state"]) == "normal"
    
    def test_timeout_result_shows_error_in_text_widget(self, app_with_map):
        """Test that timeout result shows error details in text widget.
        
        Validates: Requirement 15.6
        """
        app, mock_map = app_with_map
        
        # Create a timeout result
        timeout_result = {
            "ok": False,
            "title": "The request timed out",
            "detail": "The route request did not complete within 30 seconds."
        }
        
        # Simulate _on_result being called with timeout
        app._on_result(timeout_result)
        
        # Verify text widget shows error
        text_content = app.result_text.get("1.0", "end")
        assert "The request timed out" in text_content
        assert "did not complete within 30 seconds" in text_content
    
    def test_timeout_with_map_clear_error_continues(self, app_with_map):
        """Test that timeout handling continues even if map clear fails.
        
        Validates: User requirement 2 (error handling)
        """
        app, mock_map = app_with_map
        
        # Make clear_route raise an exception
        mock_map.clear_route.side_effect = Exception("Map clear failed")
        
        # Create a timeout result
        timeout_result = {
            "ok": False,
            "title": "The request timed out",
            "detail": "The route request did not complete within 30 seconds."
        }
        
        # Simulate _on_result being called with timeout - should not raise
        app._on_result(timeout_result)
        
        # Verify status bar still shows timeout (or map error)
        assert "timed out" in app.status_var.get().lower() or "map" in app.status_var.get().lower()
        
        # Verify button was still re-enabled
        assert str(app.search_button["state"]) == "normal"

