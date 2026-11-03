"""Unit tests for MapWidget class.

Tests verify that the MapWidget correctly renders routes, places markers,
handles edge cases, and manages state appropriately.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from src.frontend.desktop.map_widget import MapWidget, TKINTERMAPVIEW_AVAILABLE


# Skip all tests if tkintermapview is not available
pytestmark = pytest.mark.skipif(
    not TKINTERMAPVIEW_AVAILABLE,
    reason="tkintermapview not installed"
)


class TestMapWidgetRenderRoute:
    """Test suite for MapWidget.render_route() method.
    
    **Validates: Requirements 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, User requirement 2 (error handling)**
    """
    
    @pytest.fixture
    def mock_parent(self):
        """Create a mock parent widget."""
        return Mock()
    
    @pytest.fixture
    def map_widget(self, mock_parent):
        """Create MapWidget instance with mocked TkinterMapView."""
        with patch('src.frontend.desktop.map_widget.TkinterMapView') as MockMapView:
            mock_view = MagicMock()
            MockMapView.return_value = mock_view
            
            widget = MapWidget(mock_parent)
            widget.widget = mock_view
            
            # Reset mocks to clear __init__ calls
            mock_view.reset_mock()
            
            return widget
    
    def test_render_route_with_valid_coordinates(self, map_widget):
        """Test that render_route draws polyline and places markers with valid coordinates.
        
        Validates: Requirements 2.3, 3.1, 3.2
        """
        coordinates = [
            (45.5, -122.6),   # Portland
            (45.6, -122.5),
            (45.7, -122.4)
        ]
        
        # Mock return values for set_path and set_marker
        mock_polyline = Mock()
        mock_start = Mock()
        mock_dest = Mock()
        
        map_widget.widget.set_path.return_value = mock_polyline
        map_widget.widget.set_marker.side_effect = [mock_start, mock_dest]
        
        # Render the route
        map_widget.render_route(coordinates)
        
        # Verify polyline was drawn with correct parameters
        map_widget.widget.set_path.assert_called_once_with(
            coordinates,
            color="#0066CC",
            width=5
        )
        
        # Verify start marker was placed at first coordinate
        first_marker_call = map_widget.widget.set_marker.call_args_list[0]
        assert first_marker_call[0][0] == 45.5  # lat
        assert first_marker_call[0][1] == -122.6  # lon
        assert first_marker_call[1]['text'] == "Starting point"
        assert first_marker_call[1]['marker_color_circle'] == "#00AA00"
        
        # Verify destination marker was placed at last coordinate
        second_marker_call = map_widget.widget.set_marker.call_args_list[1]
        assert second_marker_call[0][0] == 45.7  # lat
        assert second_marker_call[0][1] == -122.4  # lon
        assert second_marker_call[1]['text'] == "Destination"
        assert second_marker_call[1]['marker_color_circle'] == "#DD0000"
        
        # Verify state was updated
        assert map_widget.polyline_path == mock_polyline
        assert map_widget.start_marker == mock_start
        assert map_widget.destination_marker == mock_dest
    
    def test_render_route_with_empty_list(self, map_widget):
        """Test that render_route handles empty coordinate list gracefully.
        
        Shows only base tiles without crashing.
        Validates: Requirement 2.5
        """
        coordinates = []
        
        # Render with empty list
        map_widget.render_route(coordinates)
        
        # Verify nothing was drawn
        map_widget.widget.set_path.assert_not_called()
        map_widget.widget.set_marker.assert_not_called()
        
        # Verify state remains None
        assert map_widget.polyline_path is None
        assert map_widget.start_marker is None
        assert map_widget.destination_marker is None
    
    def test_render_route_with_single_coordinate(self, map_widget):
        """Test that render_route handles single coordinate correctly.
        
        Shows only start marker, no polyline or destination marker.
        Validates: Requirement 3.3
        """
        coordinates = [(45.5, -122.6)]
        
        mock_start = Mock()
        map_widget.widget.set_marker.return_value = mock_start
        
        # Render with single coordinate
        map_widget.render_route(coordinates)
        
        # Verify no polyline was drawn (need at least 2 points)
        map_widget.widget.set_path.assert_not_called()
        
        # Verify only start marker was placed
        assert map_widget.widget.set_marker.call_count == 1
        marker_call = map_widget.widget.set_marker.call_args_list[0]
        assert marker_call[0][0] == 45.5
        assert marker_call[0][1] == -122.6
        assert marker_call[1]['text'] == "Starting point"
        assert marker_call[1]['marker_color_circle'] == "#00AA00"
        
        # Verify state
        assert map_widget.polyline_path is None
        assert map_widget.start_marker == mock_start
        assert map_widget.destination_marker is None
    
    def test_render_route_clears_previous_route(self, map_widget):
        """Test that render_route clears previous polyline and markers before rendering.
        
        Validates: User requirement 2 (proper state management)
        """
        # Set up previous route elements
        old_polyline = Mock()
        old_start = Mock()
        old_dest = Mock()
        
        map_widget.polyline_path = old_polyline
        map_widget.start_marker = old_start
        map_widget.destination_marker = old_dest
        
        # Render new route
        new_coords = [(40.7, -74.0), (40.8, -73.9)]
        map_widget.render_route(new_coords)
        
        # Verify old elements were deleted
        map_widget.widget.delete.assert_called_once_with(old_polyline)
        old_start.delete.assert_called_once()
        old_dest.delete.assert_called_once()
    
    def test_render_route_handles_polyline_failure_gracefully(self, map_widget):
        """Test that render_route continues to markers even if polyline fails.
        
        Validates: User requirement 2 (error handling)
        """
        coordinates = [(45.5, -122.6), (45.6, -122.5)]
        
        # Make set_path raise an exception
        map_widget.widget.set_path.side_effect = Exception("Polyline rendering failed")
        
        mock_start = Mock()
        mock_dest = Mock()
        map_widget.widget.set_marker.side_effect = [mock_start, mock_dest]
        
        # Should not raise exception
        map_widget.render_route(coordinates)
        
        # Verify markers were still placed despite polyline failure
        assert map_widget.widget.set_marker.call_count == 2
        assert map_widget.start_marker == mock_start
        assert map_widget.destination_marker == mock_dest
    
    def test_render_route_handles_start_marker_failure_gracefully(self, map_widget):
        """Test that render_route continues to destination marker if start marker fails.
        
        Validates: User requirement 2 (error handling)
        """
        coordinates = [(45.5, -122.6), (45.6, -122.5)]
        
        # Make first set_marker call fail, second succeed
        mock_dest = Mock()
        map_widget.widget.set_marker.side_effect = [
            Exception("Start marker failed"),
            mock_dest
        ]
        
        # Should not raise exception
        map_widget.render_route(coordinates)
        
        # Verify destination marker was still placed
        assert map_widget.widget.set_marker.call_count == 2
        assert map_widget.start_marker is None  # Failed to create
        assert map_widget.destination_marker == mock_dest
    
    def test_render_route_handles_destination_marker_failure_gracefully(self, map_widget):
        """Test that render_route continues even if destination marker fails.
        
        Validates: User requirement 2 (error handling)
        """
        coordinates = [(45.5, -122.6), (45.6, -122.5)]
        
        mock_start = Mock()
        map_widget.widget.set_marker.side_effect = [
            mock_start,
            Exception("Destination marker failed")
        ]
        
        # Should not raise exception
        map_widget.render_route(coordinates)
        
        # Verify start marker was still created
        assert map_widget.start_marker == mock_start
        assert map_widget.destination_marker is None  # Failed to create
    
    def test_render_route_handles_auto_fit_failure_gracefully(self, map_widget):
        """Test that render_route doesn't crash if auto_fit_route fails.
        
        Route remains visible at current zoom level.
        Validates: User requirement 2 (error handling)
        """
        coordinates = [(45.5, -122.6), (45.6, -122.5)]
        
        # Make fit_bounding_box fail
        map_widget.widget.fit_bounding_box.side_effect = Exception("Fit failed")
        
        # Should not raise exception
        map_widget.render_route(coordinates)
        
        # Verify route was still rendered (just not auto-fitted)
        map_widget.widget.set_path.assert_called_once()
        assert map_widget.widget.set_marker.call_count == 2
    
    def test_render_route_with_two_coordinates(self, map_widget):
        """Test render_route with exactly two coordinates (minimum for route).
        
        Validates: Requirements 2.3, 3.1, 3.2
        """
        coordinates = [(45.5, -122.6), (45.7, -122.4)]
        
        # Render the route
        map_widget.render_route(coordinates)
        
        # Verify polyline was drawn
        map_widget.widget.set_path.assert_called_once()
        
        # Verify both markers were placed
        assert map_widget.widget.set_marker.call_count == 2
    
    def test_render_route_with_many_coordinates(self, map_widget):
        """Test render_route with a long route (many waypoints).
        
        Validates: Requirements 2.3, 3.1, 3.2
        """
        # Create route with 50 waypoints
        coordinates = [(45.0 + i * 0.1, -122.0 + i * 0.1) for i in range(50)]
        
        # Render the route
        map_widget.render_route(coordinates)
        
        # Verify polyline was drawn with all coordinates
        call_args = map_widget.widget.set_path.call_args
        assert len(call_args[0][0]) == 50
        
        # Verify markers at first and last positions only
        assert map_widget.widget.set_marker.call_count == 2
        
        # Verify start marker is at first coordinate
        first_call = map_widget.widget.set_marker.call_args_list[0]
        assert first_call[0][0] == 45.0
        assert first_call[0][1] == -122.0
        
        # Verify destination marker is at last coordinate
        last_call = map_widget.widget.set_marker.call_args_list[1]
        assert last_call[0][0] == 45.0 + 49 * 0.1
        assert last_call[0][1] == -122.0 + 49 * 0.1
    
    def test_render_route_marker_colors(self, map_widget):
        """Test that render_route uses correct marker colors.
        
        Start marker: green #00AA00
        Destination marker: red #DD0000
        Validates: Requirements 3.4, 3.5
        """
        coordinates = [(45.5, -122.6), (45.7, -122.4)]
        
        map_widget.render_route(coordinates)
        
        # Check start marker color
        start_call = map_widget.widget.set_marker.call_args_list[0]
        assert start_call[1]['marker_color_circle'] == "#00AA00"
        
        # Check destination marker color
        dest_call = map_widget.widget.set_marker.call_args_list[1]
        assert dest_call[1]['marker_color_circle'] == "#DD0000"
    
    def test_render_route_marker_text(self, map_widget):
        """Test that render_route uses correct marker text labels.
        
        Validates: Requirements 3.6, 3.7
        """
        coordinates = [(45.5, -122.6), (45.7, -122.4)]
        
        map_widget.render_route(coordinates)
        
        # Check start marker text
        start_call = map_widget.widget.set_marker.call_args_list[0]
        assert start_call[1]['text'] == "Starting point"
        
        # Check destination marker text
        dest_call = map_widget.widget.set_marker.call_args_list[1]
        assert dest_call[1]['text'] == "Destination"
    
    def test_render_route_polyline_style(self, map_widget):
        """Test that render_route uses correct polyline styling.
        
        Color: #0066CC (blue)
        Width: 5 pixels
        Validates: Requirement 2.4
        """
        coordinates = [(45.5, -122.6), (45.6, -122.5), (45.7, -122.4)]
        
        map_widget.render_route(coordinates)
        
        # Check polyline parameters
        call_args = map_widget.widget.set_path.call_args
        assert call_args[1]['color'] == "#0066CC"
        assert call_args[1]['width'] == 5


class TestMapWidgetClearRoute:
    """Test suite for MapWidget.clear_route() method."""
    
    @pytest.fixture
    def mock_parent(self):
        """Create a mock parent widget."""
        return Mock()
    
    @pytest.fixture
    def map_widget(self, mock_parent):
        """Create MapWidget instance with mocked TkinterMapView."""
        with patch('src.frontend.desktop.map_widget.TkinterMapView') as MockMapView:
            mock_view = MagicMock()
            MockMapView.return_value = mock_view
            widget = MapWidget(mock_parent)
            widget.widget = mock_view
            return widget
    
    def test_clear_route_removes_all_elements(self, map_widget):
        """Test that clear_route removes polyline and all markers."""
        # Set up route elements
        mock_polyline = Mock()
        mock_start = Mock()
        mock_dest = Mock()
        
        map_widget.polyline_path = mock_polyline
        map_widget.start_marker = mock_start
        map_widget.destination_marker = mock_dest
        
        # Clear the route
        map_widget.clear_route()
        
        # Verify deletions
        map_widget.widget.delete.assert_called_once_with(mock_polyline)
        mock_start.delete.assert_called_once()
        mock_dest.delete.assert_called_once()
        
        # Verify state reset
        assert map_widget.polyline_path is None
        assert map_widget.start_marker is None
        assert map_widget.destination_marker is None
    
    def test_clear_route_handles_none_values(self, map_widget):
        """Test that clear_route handles None values gracefully."""
        # Ensure all state is None
        map_widget.polyline_path = None
        map_widget.start_marker = None
        map_widget.destination_marker = None
        
        # Should not raise exception or call delete
        map_widget.clear_route()
        
        map_widget.widget.delete.assert_not_called()
    
    def test_clear_route_handles_partial_state(self, map_widget):
        """Test that clear_route handles partial route state."""
        # Only polyline exists
        mock_polyline = Mock()
        map_widget.polyline_path = mock_polyline
        map_widget.start_marker = None
        map_widget.destination_marker = None
        
        map_widget.clear_route()
        
        # Verify only polyline was deleted
        map_widget.widget.delete.assert_called_once_with(mock_polyline)
        assert map_widget.polyline_path is None
    
    def test_clear_route_handles_deletion_failures(self, map_widget):
        """Test that clear_route continues even if deletions fail."""
        mock_polyline = Mock()
        mock_start = Mock()
        mock_dest = Mock()
        
        # Make deletions fail
        map_widget.widget.delete.side_effect = Exception("Delete failed")
        mock_start.delete.side_effect = Exception("Delete failed")
        mock_dest.delete.side_effect = Exception("Delete failed")
        
        map_widget.polyline_path = mock_polyline
        map_widget.start_marker = mock_start
        map_widget.destination_marker = mock_dest
        
        # Should not raise exception
        map_widget.clear_route()
        
        # Verify state was reset despite errors
        assert map_widget.polyline_path is None
        assert map_widget.start_marker is None
        assert map_widget.destination_marker is None


class TestMapWidgetAutoFit:
    """Test suite for MapWidget.auto_fit_route() method."""
    
    @pytest.fixture
    def mock_parent(self):
        """Create a mock parent widget."""
        return Mock()
    
    @pytest.fixture
    def map_widget(self, mock_parent):
        """Create MapWidget instance with mocked TkinterMapView."""
        with patch('src.frontend.desktop.map_widget.TkinterMapView') as MockMapView:
            mock_view = MagicMock()
            MockMapView.return_value = mock_view
            widget = MapWidget(mock_parent)
            widget.widget = mock_view
            # Reset mock to clear __init__ calls
            mock_view.reset_mock()
            return widget
    
    def test_auto_fit_with_multiple_coordinates(self, map_widget):
        """Test that auto_fit_route calculates correct bounding box."""
        coordinates = [
            (45.5, -122.6),
            (45.7, -122.4),
            (45.6, -122.5)
        ]
        
        map_widget.auto_fit_route(coordinates)
        
        # Verify fit_bounding_box was called
        map_widget.widget.fit_bounding_box.assert_called_once()
        
        # Check bounding box corners
        call_args = map_widget.widget.fit_bounding_box.call_args[0]
        north_west = call_args[0]
        south_east = call_args[1]
        
        # North-west should have max_lat, min_lon
        assert north_west[0] == 45.7  # max lat
        assert north_west[1] == -122.6  # min lon
        
        # South-east should have min_lat, max_lon
        assert south_east[0] == 45.5  # min lat
        assert south_east[1] == -122.4  # max lon
    
    def test_auto_fit_with_single_coordinate(self, map_widget):
        """Test that auto_fit_route centers on single coordinate at zoom 15."""
        coordinates = [(45.5, -122.6)]
        
        map_widget.auto_fit_route(coordinates)
        
        # Verify position and zoom were set, not fit_bounding_box
        map_widget.widget.set_position.assert_called_once_with(45.5, -122.6)
        map_widget.widget.set_zoom.assert_called_once_with(15)
        map_widget.widget.fit_bounding_box.assert_not_called()
    
    def test_auto_fit_with_empty_list(self, map_widget):
        """Test that auto_fit_route handles empty list gracefully."""
        coordinates = []
        
        map_widget.auto_fit_route(coordinates)
        
        # Should not call any positioning methods
        map_widget.widget.fit_bounding_box.assert_not_called()
        map_widget.widget.set_position.assert_not_called()
        map_widget.widget.set_zoom.assert_not_called()
    
    def test_auto_fit_fallback_without_fit_bounding_box(self, map_widget):
        """Test auto_fit_route falls back if fit_bounding_box not available."""
        coordinates = [(45.5, -122.6), (45.7, -122.4)]
        
        # Make fit_bounding_box raise AttributeError
        map_widget.widget.fit_bounding_box.side_effect = AttributeError()
        
        map_widget.auto_fit_route(coordinates)
        
        # Verify fallback to manual positioning
        # Should center on midpoint
        map_widget.widget.set_position.assert_called_once_with(45.6, -122.5)
        map_widget.widget.set_zoom.assert_called_once_with(10)
    
    def test_auto_fit_calculates_geographic_midpoint(self, map_widget):
        """Test that auto_fit_route calculates correct geographic midpoint.
        
        Validates: Requirement 4.3 - Calculate geographic midpoint
        """
        # Use coordinates with clear min/max values
        coordinates = [
            (40.0, -120.0),  # min lat, min lon
            (50.0, -110.0),  # max lat, max lon
            (45.0, -115.0)   # middle point
        ]
        
        # Force fallback to test midpoint calculation explicitly
        map_widget.widget.fit_bounding_box.side_effect = AttributeError()
        
        map_widget.auto_fit_route(coordinates)
        
        # Verify midpoint: ((40 + 50) / 2, (-120 + -110) / 2) = (45.0, -115.0)
        map_widget.widget.set_position.assert_called_once_with(45.0, -115.0)
    
    def test_auto_fit_handles_error_gracefully(self, map_widget):
        """Test that auto_fit_route handles unexpected errors gracefully.
        
        Validates: User requirement 2 (error handling)
        """
        coordinates = [(45.5, -122.6), (45.7, -122.4)]
        
        # Make fit_bounding_box raise unexpected error
        map_widget.widget.fit_bounding_box.side_effect = RuntimeError("Unexpected error")
        
        # Should not raise exception - error is logged
        map_widget.auto_fit_route(coordinates)
        
        # Verify execution completed (no crash)


class TestMapWidgetResetView:
    """Test suite for MapWidget.reset_view() method."""
    
    @pytest.fixture
    def mock_parent(self):
        """Create a mock parent widget."""
        return Mock()
    
    @pytest.fixture
    def map_widget(self, mock_parent):
        """Create MapWidget instance with mocked TkinterMapView."""
        with patch('src.frontend.desktop.map_widget.TkinterMapView') as MockMapView:
            mock_view = MagicMock()
            MockMapView.return_value = mock_view
            widget = MapWidget(mock_parent)
            widget.widget = mock_view
            mock_view.reset_mock()  # Clear init calls
            return widget
    
    def test_reset_view_returns_to_default(self, map_widget):
        """Test that reset_view returns to default position."""
        map_widget.reset_view()
        
        # Verify default position and zoom
        map_widget.widget.set_position.assert_called_once_with(0.0, 0.0)
        map_widget.widget.set_zoom.assert_called_once_with(2)
    
    def test_reset_view_handles_errors(self, map_widget):
        """Test that reset_view handles errors gracefully."""
        map_widget.widget.set_position.side_effect = Exception("Reset failed")
        
        # Should not raise exception
        map_widget.reset_view()


class TestMapWidgetInitialization:
    """Test suite for MapWidget.__init__() method."""
    
    @pytest.fixture
    def mock_parent(self):
        """Create a mock parent widget."""
        return Mock()
    
    def test_init_configures_tile_server(self, mock_parent):
        """Test that __init__ configures OpenStreetMap tile server."""
        with patch('src.frontend.desktop.map_widget.TkinterMapView') as MockMapView:
            mock_view = MagicMock()
            MockMapView.return_value = mock_view
            
            widget = MapWidget(mock_parent)
            
            # Verify tile server was configured
            mock_view.set_tile_server.assert_called_once_with(
                "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}",
                max_zoom=22
            )
    
    def test_init_sets_default_position(self, mock_parent):
        """Test that __init__ sets default position to (0, 0) zoom 2."""
        with patch('src.frontend.desktop.map_widget.TkinterMapView') as MockMapView:
            mock_view = MagicMock()
            MockMapView.return_value = mock_view
            
            widget = MapWidget(mock_parent)
            
            # Verify default position
            mock_view.set_position.assert_called_once_with(0.0, 0.0)
            mock_view.set_zoom.assert_called_once_with(2)
    
    def test_init_initializes_state_variables(self, mock_parent):
        """Test that __init__ initializes state variables to None."""
        with patch('src.frontend.desktop.map_widget.TkinterMapView') as MockMapView:
            mock_view = MagicMock()
            MockMapView.return_value = mock_view
            
            widget = MapWidget(mock_parent)
            
            # Verify state
            assert widget.polyline_path is None
            assert widget.start_marker is None
            assert widget.destination_marker is None
    
    def test_init_raises_on_missing_library(self, mock_parent):
        """Test that __init__ raises ImportError if tkintermapview missing."""
        with patch('src.frontend.desktop.map_widget.TKINTERMAPVIEW_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                widget = MapWidget(mock_parent)
            
            assert "tkintermapview is not installed" in str(exc_info.value)
    
    def test_get_widget_returns_underlying_widget(self, mock_parent):
        """Test that get_widget() returns the TkinterMapView instance."""
        with patch('src.frontend.desktop.map_widget.TkinterMapView') as MockMapView:
            mock_view = MagicMock()
            MockMapView.return_value = mock_view
            
            widget = MapWidget(mock_parent)
            
            assert widget.get_widget() == mock_view
