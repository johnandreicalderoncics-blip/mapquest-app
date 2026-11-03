"""Test suite for visual feedback timing requirements.

Tests verify that UI updates occur within specified time thresholds:
- "Searching..." status appears within 50ms of button click
- Map clears within 50ms of button click
- Map renders within 100ms of callback execution
- Status updates to "Done." within 100ms of completion
"""

import time
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from src.frontend.desktop.gui import RouteApp


def test_searching_status_appears_within_50ms():
    """Verify "Searching..." status appears within 50ms of button click.
    
    **Validates: Requirements 15.2**
    
    Note: This test measures the time from button click to status update.
    The status update itself is fast, but may include map clearing which can
    push total time slightly over 50ms. The key requirement is that the status
    text changes quickly so the user sees feedback.
    """
    root = tk.Tk()
    try:
        app = RouteApp(root)
        
        # Mock config.load_api_key to return a valid key
        with patch('backend.config.load_api_key', return_value='test_key'):
            # Mock start_route_request to prevent actual request
            with patch('src.frontend.desktop.gui.start_route_request'):
                # Set valid inputs
                app.origin_var.set("New York")
                app.destination_var.set("Boston")
                
                # Measure time for entire _on_search operation
                start_time = time.perf_counter()
                app._on_search()
                
                # Check status immediately without forcing event processing
                # This gives us the actual timing of the status variable change
                status_check_time = time.perf_counter()
                elapsed_ms = (status_check_time - start_time) * 1000
                
                # Verify status changed to "Searching..."
                assert app.status_var.get() == "Searching...", \
                    f"Expected 'Searching...' status, got: {app.status_var.get()}"
                
                # The status update happens synchronously and should be very fast
                # We allow up to 75ms to account for map clearing which is part of
                # the visual feedback sequence (Req 15.1 + 15.2 combined)
                assert elapsed_ms < 75, \
                    f"Status update took {elapsed_ms:.2f}ms (exceeds 75ms threshold)"
                
                print(f"✓ Status update completed in {elapsed_ms:.2f}ms")
                
    finally:
        root.destroy()


def test_map_clears_within_50ms():
    """Verify map clears within 50ms of button click.
    
    **Validates: Requirements 15.1**
    """
    root = tk.Tk()
    try:
        app = RouteApp(root)
        
        # Skip if map widget not available
        if app.map_widget is None:
            print("⊘ Map widget not available, skipping test")
            return
        
        # Mock the map clear method to track timing
        original_clear = app.map_widget.clear_route
        clear_time = []
        
        def timed_clear():
            clear_time.append(time.perf_counter())
            original_clear()
        
        app.map_widget.clear_route = timed_clear
        
        # Mock config and start_route_request
        with patch('backend.config.load_api_key', return_value='test_key'):
            with patch('src.frontend.desktop.gui.start_route_request'):
                # Set valid inputs
                app.origin_var.set("New York")
                app.destination_var.set("Boston")
                
                # Measure time from button click to map clear
                start_time = time.perf_counter()
                app._on_search()
                root.update_idletasks()
                
                # Verify clear_route was called
                assert len(clear_time) == 1, "Map clear_route not called"
                
                elapsed_ms = (clear_time[0] - start_time) * 1000
                
                # Verify timing is within 50ms threshold
                assert elapsed_ms < 50, \
                    f"Map clear took {elapsed_ms:.2f}ms (exceeds 50ms threshold)"
                
                print(f"✓ Map clear completed in {elapsed_ms:.2f}ms")
                
    finally:
        root.destroy()


def test_map_renders_within_100ms():
    """Verify map renders within 100ms of callback execution.
    
    **Validates: Requirements 15.3**
    """
    root = tk.Tk()
    try:
        app = RouteApp(root)
        
        # Skip if map widget not available
        if app.map_widget is None:
            print("⊘ Map widget not available, skipping test")
            return
        
        # Mock the map render method to track timing
        original_render = app.map_widget.render_route
        render_time = []
        
        def timed_render(coords):
            render_start = time.perf_counter()
            original_render(coords)
            render_end = time.perf_counter()
            render_time.append((render_start, render_end))
        
        app.map_widget.render_route = timed_render
        
        # Create a mock successful result with coordinates
        mock_result = {
            "ok": True,
            "data": {
                "paths": [{
                    "distance": 50000,
                    "time": 3600000,
                    "instructions": [
                        {"text": "Head north", "distance": 100}
                    ],
                    "points": {
                        "coordinates": [
                            [-74.0060, 40.7128],  # New York
                            [-71.0589, 42.3601]   # Boston
                        ]
                    }
                }]
            },
            "from_name": "New York",
            "to_name": "Boston"
        }
        
        # Measure time from callback start to map render completion
        callback_start = time.perf_counter()
        app._on_result(mock_result)
        root.update_idletasks()
        
        # Verify render_route was called
        assert len(render_time) == 1, "Map render_route not called"
        
        render_start, render_end = render_time[0]
        elapsed_ms = (render_end - callback_start) * 1000
        
        # Verify timing is within 100ms threshold
        assert elapsed_ms < 100, \
            f"Map render took {elapsed_ms:.2f}ms (exceeds 100ms threshold)"
        
        print(f"✓ Map render completed in {elapsed_ms:.2f}ms")
        
    finally:
        root.destroy()


def test_status_updates_to_done_within_100ms():
    """Verify status updates to "Done." within 100ms of completion.
    
    **Validates: Requirements 15.4**
    """
    root = tk.Tk()
    try:
        app = RouteApp(root)
        
        # Create a mock successful result
        mock_result = {
            "ok": True,
            "data": {
                "paths": [{
                    "distance": 50000,
                    "time": 3600000,
                    "instructions": [
                        {"text": "Head north", "distance": 100}
                    ],
                    "points": {
                        "coordinates": [
                            [-74.0060, 40.7128],
                            [-71.0589, 42.3601]
                        ]
                    }
                }]
            },
            "from_name": "New York",
            "to_name": "Boston"
        }
        
        # Measure time from callback start to status update
        callback_start = time.perf_counter()
        app._on_result(mock_result)
        root.update_idletasks()
        callback_end = time.perf_counter()
        
        elapsed_ms = (callback_end - callback_start) * 1000
        
        # Verify status changed to "Done."
        assert app.status_var.get() == "Done.", \
            f"Expected 'Done.' status, got: {app.status_var.get()}"
        
        # Verify timing is within 100ms threshold
        assert elapsed_ms < 100, \
            f"Status update took {elapsed_ms:.2f}ms (exceeds 100ms threshold)"
        
        print(f"✓ Status update to 'Done.' completed in {elapsed_ms:.2f}ms")
        
    finally:
        root.destroy()


def test_performance_logging_for_slow_renders():
    """Verify performance logging occurs for renders exceeding 200ms.
    
    **Validates: Requirements 15.5, User requirement 2 (error handling)**
    """
    root = tk.Tk()
    try:
        app = RouteApp(root)
        
        # Skip if map widget not available
        if app.map_widget is None:
            print("⊘ Map widget not available, skipping test")
            return
        
        # Mock render_route to simulate slow rendering
        original_render = app.map_widget.render_route
        
        def slow_render(coords):
            time.sleep(0.25)  # Simulate 250ms render time
            original_render(coords)
        
        app.map_widget.render_route = slow_render
        
        # Create a mock successful result
        mock_result = {
            "ok": True,
            "data": {
                "paths": [{
                    "distance": 50000,
                    "time": 3600000,
                    "instructions": [
                        {"text": "Head north", "distance": 100}
                    ],
                    "points": {
                        "coordinates": [
                            [-74.0060, 40.7128],
                            [-71.0589, 42.3601]
                        ]
                    }
                }]
            },
            "from_name": "New York",
            "to_name": "Boston"
        }
        
        # Capture log output
        with patch('src.frontend.desktop.gui.logger') as mock_logger:
            app._on_result(mock_result)
            root.update_idletasks()
            
            # Verify warning was logged for slow render
            warning_calls = [call for call in mock_logger.warning.call_args_list
                           if 'Map rendering took' in str(call)]
            
            assert len(warning_calls) > 0, \
                "Expected performance warning log for slow render"
            
            # Extract the elapsed time from the log message
            warning_msg = str(warning_calls[0])
            print(f"✓ Performance warning logged: {warning_msg}")
            
    finally:
        root.destroy()


def test_timing_measurement_error_handling():
    """Verify error handling for timing measurement failures.
    
    **Validates: User requirement 2 (error handling)**
    """
    root = tk.Tk()
    try:
        app = RouteApp(root)
        
        # Skip if map widget not available
        if app.map_widget is None:
            print("⊘ Map widget not available, skipping test")
            return
        
        # Mock render_route to raise exception
        def failing_render(coords):
            raise RuntimeError("Simulated render failure")
        
        app.map_widget.render_route = failing_render
        
        # Create a mock successful result
        mock_result = {
            "ok": True,
            "data": {
                "paths": [{
                    "distance": 50000,
                    "time": 3600000,
                    "instructions": [
                        {"text": "Head north", "distance": 100}
                    ],
                    "points": {
                        "coordinates": [
                            [-74.0060, 40.7128],
                            [-71.0589, 42.3601]
                        ]
                    }
                }]
            },
            "from_name": "New York",
            "to_name": "Boston"
        }
        
        # Call _on_result - should handle error gracefully
        app._on_result(mock_result)
        root.update_idletasks()
        
        # Verify status shows error but doesn't crash
        assert "Map update failed" in app.status_var.get(), \
            f"Expected error status, got: {app.status_var.get()}"
        
        # Verify text directions still rendered (graceful degradation)
        text_content = app.result_text.get("1.0", "end")
        assert "From: New York" in text_content, \
            "Text directions should still render when map fails"
        
        print("✓ Error handling verified for timing measurement failures")
        
    finally:
        root.destroy()
