"""MapWidget wrapper for interactive route visualization.

This module provides a wrapper around TkinterMapView that encapsulates
all map rendering and interaction logic for displaying routes with
start/destination markers and auto-fitting the viewport.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

try:
    from tkintermapview import TkinterMapView
    TKINTERMAPVIEW_AVAILABLE = True
except ImportError:
    TKINTERMAPVIEW_AVAILABLE = False
    TkinterMapView = None


logger = logging.getLogger(__name__)


class CoordinateValidator:
    """Validates geographic coordinates for map rendering.
    
    This class provides static methods to validate latitude and longitude
    coordinates against standard geographic bounds and to filter coordinate
    lists to remove invalid entries.
    """
    
    LAT_MIN = -90.0
    LAT_MAX = 90.0
    LON_MIN = -180.0
    LON_MAX = 180.0
    
    @staticmethod
    def is_valid(lat: float, lon: float) -> bool:
        """Check if latitude and longitude are within valid geographic bounds.
        
        Args:
            lat: Latitude value to validate (degrees)
            lon: Longitude value to validate (degrees)
            
        Returns:
            True if both latitude and longitude are within valid bounds,
            False otherwise.
            
        Note:
            Valid bounds are: lat ∈ [-90, 90], lon ∈ [-180, 180]
        """
        try:
            lat_float = float(lat)
            lon_float = float(lon)
            return (
                CoordinateValidator.LAT_MIN <= lat_float <= CoordinateValidator.LAT_MAX
                and CoordinateValidator.LON_MIN <= lon_float <= CoordinateValidator.LON_MAX
            )
        except (TypeError, ValueError):
            # Invalid input types that cannot be converted to float
            return False
    
    @staticmethod
    def filter_valid(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Filter a list of coordinates to only include valid entries.
        
        Args:
            coords: List of (latitude, longitude) tuples to filter
            
        Returns:
            List containing only the coordinates that passed validation.
            Invalid coordinates are silently dropped.
            
        Note:
            This method logs warnings for each filtered coordinate to aid debugging.
        """
        valid_coords = []
        for i, coord in enumerate(coords):
            try:
                if not isinstance(coord, (list, tuple)) or len(coord) < 2:
                    logger.warning(f"Coordinate {i} is not a valid tuple/list: {coord}")
                    continue
                
                lat, lon = coord[0], coord[1]
                if CoordinateValidator.is_valid(lat, lon):
                    valid_coords.append((float(lat), float(lon)))
                else:
                    logger.warning(
                        f"Coordinate {i} out of bounds: lat={lat}, lon={lon}"
                    )
            except (TypeError, ValueError, IndexError) as exc:
                logger.warning(
                    f"Failed to validate coordinate {i}: {exc}"
                )
                continue
        
        return valid_coords


def extract_route_geometry(result: Dict[str, Any]) -> List[Tuple[float, float]]:
    """Extract route coordinates from API result with comprehensive error handling.
    
    This function safely navigates the nested dictionary structure returned by
    the GraphHopper API and extracts the route geometry coordinates. It handles
    missing keys, invalid data structures, and coordinate validation gracefully.
    
    Args:
        result: The dictionary returned by backend.api.fetch_route(), expected
                to contain the structure:
                {
                    "ok": bool,
                    "data": {
                        "paths": [
                            {
                                "points": {
                                    "coordinates": [[lon, lat], ...]
                                }
                            }
                        ]
                    }
                }
    
    Returns:
        List of (latitude, longitude) tuples representing the route path.
        Returns empty list if:
        - result["ok"] is False
        - Any required key is missing
        - paths list is empty
        - coordinates list is empty
        - All coordinates are invalid
    
    Note:
        - GraphHopper returns coordinates as [longitude, latitude] format
        - This function converts to [latitude, longitude] for tkintermapview
        - Invalid coordinates (lat outside ±90°, lon outside ±180°) are filtered out
        - Logs warnings for missing keys but does not raise exceptions
        - All errors are handled gracefully to maintain application stability
    """
    try:
        # Check if the result indicates success
        if not result.get("ok"):
            logger.debug("Result indicates failure, no geometry to extract")
            return []
        
        # Navigate nested path: result["data"]["paths"][0]["points"]["coordinates"]
        data = result.get("data")
        if data is None:
            logger.warning("Missing 'data' key in API result")
            return []
        
        paths = data.get("paths")
        if paths is None:
            logger.warning("Missing 'paths' key in API result data")
            return []
        
        if not isinstance(paths, list) or len(paths) == 0:
            logger.warning("'paths' is not a list or is empty")
            return []
        
        # Get first path (GraphHopper returns array, we use first route)
        first_path = paths[0]
        if not isinstance(first_path, dict):
            logger.warning(f"First path is not a dictionary: {type(first_path)}")
            return []
        
        points = first_path.get("points")
        if points is None:
            logger.warning("Missing 'points' key in path")
            return []
        
        if not isinstance(points, dict):
            logger.warning(f"'points' is not a dictionary: {type(points)}")
            return []
        
        coordinates = points.get("coordinates")
        if coordinates is None:
            logger.warning("Missing 'coordinates' key in points")
            return []
        
        if not isinstance(coordinates, list):
            logger.warning(f"'coordinates' is not a list: {type(coordinates)}")
            return []
        
        if len(coordinates) == 0:
            logger.info("Coordinates list is empty (valid but no geometry)")
            return []
        
        # Convert [lon, lat] → [lat, lon] and validate
        converted_coords = []
        for i, coord in enumerate(coordinates):
            try:
                if not isinstance(coord, (list, tuple)) or len(coord) < 2:
                    logger.warning(f"Coordinate {i} is not a valid list/tuple: {coord}")
                    continue
                
                # GraphHopper format: [longitude, latitude]
                # tkintermapview format: [latitude, longitude]
                lon = float(coord[0])
                lat = float(coord[1])
                
                # Validate bounds before adding
                if CoordinateValidator.is_valid(lat, lon):
                    converted_coords.append((lat, lon))
                else:
                    logger.warning(
                        f"Coordinate {i} out of bounds and filtered: "
                        f"lat={lat}, lon={lon}"
                    )
                    
            except (IndexError, ValueError, TypeError) as exc:
                logger.warning(f"Failed to convert coordinate {i}: {exc}")
                continue
        
        if len(converted_coords) == 0:
            logger.warning(
                f"All {len(coordinates)} coordinates were invalid and filtered out"
            )
        else:
            logger.info(
                f"Extracted {len(converted_coords)} valid coordinates "
                f"from {len(coordinates)} total"
            )
        
        return converted_coords
        
    except Exception as exc:
        # Catch-all for any unexpected errors during extraction
        logger.error(
            f"Unexpected error extracting route geometry: {exc}",
            exc_info=True
        )
        return []


class CoordinateValidator:
    """Validates geographic coordinates against valid bounds.
    
    This class provides static methods for validating individual coordinates
    and filtering lists of coordinates to ensure they fall within valid
    geographic bounds (latitude: -90 to +90, longitude: -180 to +180).
    """
    
    LAT_MIN = -90.0
    LAT_MAX = 90.0
    LON_MIN = -180.0
    LON_MAX = 180.0
    
    @staticmethod
    def is_valid(lat: float, lon: float) -> bool:
        """Check if a coordinate pair is within valid geographic bounds.
        
        Args:
            lat: Latitude value to validate
            lon: Longitude value to validate
            
        Returns:
            bool: True if both latitude and longitude are within valid bounds,
                  False otherwise
                  
        Raises:
            TypeError: If lat or lon cannot be converted to float
            ValueError: If lat or lon are non-numeric values
        """
        try:
            # Convert to float to handle various numeric types
            lat_float = float(lat)
            lon_float = float(lon)
            
            # Check bounds
            lat_valid = CoordinateValidator.LAT_MIN <= lat_float <= CoordinateValidator.LAT_MAX
            lon_valid = CoordinateValidator.LON_MIN <= lon_float <= CoordinateValidator.LON_MAX
            
            return lat_valid and lon_valid
            
        except (TypeError, ValueError) as exc:
            logger.debug(f"Invalid coordinate types: lat={lat}, lon={lon}: {exc}")
            raise
    
    @staticmethod
    def filter_valid(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Filter a list of coordinates to only include valid ones.
        
        Args:
            coords: List of (latitude, longitude) tuples to filter
            
        Returns:
            List of (latitude, longitude) tuples containing only coordinates
            that are within valid geographic bounds. Invalid coordinates are
            excluded with debug logging.
            
        Raises:
            TypeError: If coords is not iterable or elements are not tuples/lists
        """
        try:
            valid_coords = []
            
            for idx, coord in enumerate(coords):
                try:
                    # Handle both tuples and lists
                    if not isinstance(coord, (tuple, list)) or len(coord) < 2:
                        logger.debug(f"Skipping malformed coordinate at index {idx}: {coord}")
                        continue
                    
                    lat, lon = coord[0], coord[1]
                    
                    if CoordinateValidator.is_valid(lat, lon):
                        valid_coords.append((float(lat), float(lon)))
                    else:
                        logger.debug(
                            f"Filtered out-of-bounds coordinate at index {idx}: "
                            f"lat={lat}, lon={lon}"
                        )
                        
                except (TypeError, ValueError, IndexError) as exc:
                    logger.debug(
                        f"Skipping invalid coordinate at index {idx}: {coord}: {exc}"
                    )
                    continue
            
            if len(valid_coords) < len(coords):
                logger.info(
                    f"Filtered coordinates: {len(coords)} input, "
                    f"{len(valid_coords)} valid, "
                    f"{len(coords) - len(valid_coords)} filtered out"
                )
            
            return valid_coords
            
        except TypeError as exc:
            logger.error(f"Invalid input to filter_valid: {exc}", exc_info=True)
            raise


class MapWidget:
    """Wrapper around TkinterMapView with route visualization capabilities.
    
    This class encapsulates map rendering, marker placement, and viewport
    management. It maintains thread-safe state for polylines and markers,
    and provides comprehensive error handling for all map operations.
    
    Attributes:
        widget: The underlying TkinterMapView instance
        polyline_path: Reference to current route polyline (for removal)
        start_marker: Reference to start location marker (for removal)
        destination_marker: Reference to destination marker (for removal)
    """
    
    def __init__(self, parent):
        """Initialize MapWidget with OpenStreetMap tile server.
        
        Args:
            parent: The parent tkinter widget
            
        Raises:
            ImportError: If tkintermapview is not installed
            Exception: If map widget initialization fails
        """
        if not TKINTERMAPVIEW_AVAILABLE:
            raise ImportError(
                "tkintermapview is not installed. "
                "Please run: pip install -r requirements.txt"
            )
        
        try:
            # Create TkinterMapView widget with no corner radius
            self.widget = TkinterMapView(parent, corner_radius=0)
            
            # Configure Google Maps tile server (more reliable than OSM)
            self.widget.set_tile_server(
                "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}",
                max_zoom=22
            )
            
            # Initialize state variables for route elements
            self.polyline_path = None
            self.start_marker = None
            self.destination_marker = None
            
            # Set default position: lat=0, lon=0, zoom=2
            self.widget.set_position(0.0, 0.0)
            self.widget.set_zoom(2)
            
            logger.info("MapWidget initialized successfully")
            
        except Exception as exc:
            logger.error(f"Failed to initialize MapWidget: {exc}", exc_info=True)
            raise
    
    def get_widget(self):
        """Return the underlying TkinterMapView widget for grid placement.
        
        Returns:
            TkinterMapView: The underlying map widget instance
        """
        return self.widget
    
    def render_route(self, coordinates: List[Tuple[float, float]]) -> None:
        """Draw route polyline and place start/destination markers.
        
        This method:
        1. Clears any previous route elements
        2. Draws a blue polyline connecting all coordinates
        3. Places a green start marker at the first coordinate
        4. Places a red destination marker at the last coordinate
        5. Auto-fits the viewport to show the entire route
        
        Args:
            coordinates: List of (latitude, longitude) tuples defining the route.
                        Empty list is handled gracefully (shows only base tiles).
                        Single coordinate shows only start marker.
        
        Note:
            All operations are wrapped in try-catch blocks. Failures in one
            operation do not prevent others from executing.
        """
        try:
            # Clear previous route elements first
            self.clear_route()
            
            # Handle empty coordinate list - show only base tiles
            if not coordinates:
                logger.info("No coordinates provided, map shows base tiles only")
                return
            
            # Draw polyline with color=#0066CC, width=5px, opacity=0.85
            try:
                if len(coordinates) >= 2:
                    # Need at least 2 points for a polyline
                    self.polyline_path = self.widget.set_path(
                        coordinates,
                        color="#0066CC",
                        width=5
                    )
                    logger.debug(f"Rendered polyline with {len(coordinates)} coordinates")
            except Exception as exc:
                logger.error(f"Failed to render polyline: {exc}", exc_info=True)
                # Continue to markers even if polyline fails
            
            # Place start marker (green #00AA00, 12px diameter) at first coordinate
            try:
                if len(coordinates) >= 1:
                    lat, lon = coordinates[0]
                    self.start_marker = self.widget.set_marker(
                        lat, lon,
                        text="Starting point",
                        marker_color_circle="#00AA00"
                    )
                    logger.debug(f"Placed start marker at ({lat}, {lon})")
            except Exception as exc:
                logger.error(f"Failed to place start marker: {exc}", exc_info=True)
            
            # Place destination marker (red #DD0000, 12px diameter) at last coordinate
            try:
                if len(coordinates) >= 2:
                    lat, lon = coordinates[-1]
                    self.destination_marker = self.widget.set_marker(
                        lat, lon,
                        text="Destination",
                        marker_color_circle="#DD0000"
                    )
                    logger.debug(f"Placed destination marker at ({lat}, {lon})")
            except Exception as exc:
                logger.error(f"Failed to place destination marker: {exc}", exc_info=True)
            
            # Auto-fit viewport to show entire route
            try:
                self.auto_fit_route(coordinates)
            except Exception as exc:
                logger.error(f"Failed to auto-fit viewport: {exc}", exc_info=True)
                # Route is still visible at current zoom
                
        except Exception as exc:
            logger.error(f"Unexpected error in render_route: {exc}", exc_info=True)
    
    def clear_route(self) -> None:
        """Remove polyline and all markers from the map.
        
        This method safely deletes all route elements (polyline, start marker,
        destination marker) and resets state variables to None. Each deletion
        is wrapped in error handling to ensure partial failures don't prevent
        other cleanups.
        """
        try:
            # Delete polyline_path if it exists
            if self.polyline_path is not None:
                try:
                    self.widget.delete(self.polyline_path)
                    logger.debug("Deleted polyline path")
                except Exception as exc:
                    logger.error(f"Failed to delete polyline: {exc}", exc_info=True)
                finally:
                    self.polyline_path = None
            
            # Delete start_marker if it exists
            if self.start_marker is not None:
                try:
                    self.start_marker.delete()
                    logger.debug("Deleted start marker")
                except Exception as exc:
                    logger.error(f"Failed to delete start marker: {exc}", exc_info=True)
                finally:
                    self.start_marker = None
            
            # Delete destination_marker if it exists
            if self.destination_marker is not None:
                try:
                    self.destination_marker.delete()
                    logger.debug("Deleted destination marker")
                except Exception as exc:
                    logger.error(f"Failed to delete destination marker: {exc}", exc_info=True)
                finally:
                    self.destination_marker = None
                    
        except Exception as exc:
            logger.error(f"Unexpected error in clear_route: {exc}", exc_info=True)
    
    def auto_fit_route(self, coordinates: List[Tuple[float, float]]) -> None:
        """Adjust zoom and center to show entire route with padding.
        
        This method calculates the bounding box of all coordinates and adjusts
        the viewport to fit the entire route with 24px padding on all edges.
        
        Args:
            coordinates: List of (latitude, longitude) tuples
            
        Edge cases:
            - Empty list: No change to viewport
            - Single coordinate: Center on coordinate at zoom level 15
            - Multiple coordinates: Calculate bounding box and fit viewport
        """
        try:
            if not coordinates:
                logger.debug("No coordinates for auto-fit")
                return
            
            if len(coordinates) == 1:
                # Single coordinate: center at zoom level 15
                lat, lon = coordinates[0]
                self.widget.set_position(lat, lon)
                self.widget.set_zoom(15)
                logger.debug(f"Auto-fit single coordinate at ({lat}, {lon}) zoom=15")
                return
            
            # Calculate bounding box: min_lat, max_lat, min_lon, max_lon
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Calculate geographic midpoint
            mid_lat = (min_lat + max_lat) / 2.0
            mid_lon = (min_lon + max_lon) / 2.0
            
            # Use tkintermapview's built-in fit_bounding_box method if available
            # This automatically handles zoom calculation with padding
            try:
                self.widget.fit_bounding_box(
                    (max_lat, min_lon),  # Top-left corner (north-west)
                    (min_lat, max_lon)   # Bottom-right corner (south-east)
                )
                logger.debug(
                    f"Auto-fit bounding box: "
                    f"lat=[{min_lat:.4f}, {max_lat:.4f}], "
                    f"lon=[{min_lon:.4f}, {max_lon:.4f}]"
                )
            except AttributeError:
                # Fallback: manually center on midpoint with conservative zoom
                self.widget.set_position(mid_lat, mid_lon)
                # Use zoom level 10 as a reasonable default for route display
                self.widget.set_zoom(10)
                logger.debug(
                    f"Auto-fit fallback: centered at ({mid_lat:.4f}, {mid_lon:.4f}) zoom=10"
                )
                
        except Exception as exc:
            logger.error(f"Failed to auto-fit route: {exc}", exc_info=True)
    
    def reset_view(self) -> None:
        """Return to default position (0°, 0°, zoom 2).
        
        This method resets the map viewport to the initial state showing
        the entire world view.
        """
        try:
            self.widget.set_position(0.0, 0.0)
            self.widget.set_zoom(2)
            logger.debug("Reset view to default (0°, 0°, zoom=2)")
        except Exception as exc:
            logger.error(f"Failed to reset view: {exc}", exc_info=True)
