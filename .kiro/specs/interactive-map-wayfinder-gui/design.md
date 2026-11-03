# Design Document: Interactive Map Wayfinder GUI

## Overview

The Interactive Map Wayfinder GUI feature transforms the existing text-based tkinter desktop application into a modern, visually rich mapping experience inspired by Google Maps. Users will see their routes rendered on an interactive map with pan and zoom capabilities, alongside traditional turn-by-turn text directions. The design prioritizes visual clarity, intuitive interaction patterns, and seamless integration with the existing backend architecture.

### Design Philosophy

**Modern Minimalism with Purpose**
- Clean, uncluttered interface that puts the map front and center
- Information hierarchy that guides users naturally from input to visualization
- Purposeful use of whitespace and visual separation
- Progressive disclosure: show essentials first, details on interaction

**Google Maps-Inspired Interaction Model**
- Familiar pan-and-zoom gestures that feel natural to anyone who has used digital maps
- Instant visual feedback for all user actions
- Smooth transitions between states (idle → searching → displaying results)
- Resilient to errors without breaking the user flow

**Accessible and Responsive**
- High-contrast color choices meeting WCAG AA standards
- Clear visual states (hover, active, disabled, error)
- Responsive layout adapting to window resizing
- Keyboard accessibility for all primary actions

### Key Design Decisions

1. **Tkintermapview Integration**: Use the lightweight tkintermapview library instead of embedding a browser widget, keeping the desktop app self-contained and reducing dependencies.

2. **Vertical Layout with Fixed Proportions**: Place the map above text directions in a vertical stack, allocating space proportionally during window resize to maintain both views.

3. **Color Palette Anchored in Brand Identity**:
   - **Primary Blue (#0066CC)**: Trust, navigation, primary actions
   - **Secondary Orange (#FF6B35)**: Energy, attention, destination markers
   - **Neutral White/Gray (#FFFFFF, #F5F5F5, #E6E6E6)**: Clarity, space, backgrounds

4. **Thread-Safe Map Updates**: All map widget operations occur on the GUI thread via `root.after()`, preserving the existing threading model without introducing race conditions.

5. **Graceful Degradation**: Missing tiles display as placeholders with retry capability; route geometry extraction failures leave the map in a usable state showing only base tiles.

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          GUI Window (tkinter)                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Search Controls Frame (row 0)                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────┐  ┌──────────┐  │  │
│  │  │ Origin     │  │ Destination│  │ Units   │  │ Travel   │  │  │
│  │  │ Input      │  │ Input      │  │ Radio   │  │ Mode     │  │  │
│  │  └────────────┘  └────────────┘  └─────────┘  └──────────┘  │  │
│  │  ┌──────────────┐  ┌────────┐                                │  │
│  │  │ Find Route   │  │ Clear  │                                │  │
│  │  │ Button (Blue)│  │ Button │                                │  │
│  │  └──────────────┘  └────────┘                                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │            Map Widget (TkinterMapView) (row 1)                │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │  🗺️ Interactive Map Canvas                              │ │  │
│  │  │    • Base tiles (OpenStreetMap)                         │ │  │
│  │  │    • Route polyline (blue, 5px)                         │ │  │
│  │  │    • Start marker (green circle)                        │ │  │
│  │  │    • Destination marker (orange circle)                 │ │  │
│  │  │    • Pan: mouse drag                                    │ │  │
│  │  │    • Zoom: mouse wheel                                  │ │  │
│  │  │    • Attribution: "© OpenStreetMap contributors"        │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │        Text Directions Widget (scrollable) (row 2)            │  │
│  │  • Trip summary (from, to, mode, duration, distance, fuel)   │  │
│  │  • Numbered turn-by-turn instructions with distances         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   Status Bar (row 3)                          │  │
│  │  "Enter locations..." | "Searching..." | "Done." | Errors    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         ↕️ Threading Model: GUI Thread ↔️ Worker Thread
```

### Data Flow Architecture

```
User Action (Find Route)
    ↓
Validate Inputs (GUI thread)
    ↓
Start Worker Thread (daemon)
    ↓
Worker: backend/api.fetch_route()
    ↓
Worker: Extract route geometry from result["data"]["paths"][0]["points"]["coordinates"]
    ↓
Worker: Convert [lon, lat] → [lat, lon] format
    ↓
Worker: root.after(0, callback, result)
    ↓
GUI Thread: callback receives result
    ↓
GUI Thread: Update map widget
    │   ├─→ Clear previous polyline and markers
    │   ├─→ Render new polyline (coordinates list)
    │   ├─→ Place start marker (first coordinate)
    │   ├─→ Place destination marker (last coordinate)
    │   └─→ Auto-fit viewport to bounding box
    ↓
GUI Thread: Update text directions widget
    ↓
GUI Thread: Update status bar
```

### Component Relationships

```
gui.py (RouteApp class)
    │
    ├─→ TkinterMapView instance (map_widget)
    │       ├─→ set_position() - pan to coordinates
    │       ├─→ set_zoom() - adjust zoom level
    │       ├─→ set_path() - draw route polyline
    │       ├─→ set_marker() - place start/destination markers
    │       └─→ delete_all_marker() - clear markers
    │
    ├─→ tk.Text instance (result_text)
    │       └─→ displays formatted directions via result_to_lines()
    │
    ├─→ backend/api.py
    │       └─→ fetch_route() returns {"ok", "data", "from_name", "to_name"}
    │
    ├─→ backend/formatting.py
    │       ├─→ format_distance(meters, units)
    │       ├─→ format_time(milliseconds)
    │       └─→ format_fuel_estimate(meters, units, profile)
    │
    └─→ backend/config.py
            └─→ load_api_key() returns key or None
```

## UI/UX Design Specification

### Color Palette

**Primary Colors**
- **Primary Blue**: `#0066CC` (RGB 0, 102, 204)
  - Usage: Route polylines, "Find Route" button, active states, links
  - Conveys: Trust, reliability, navigation
  - Accessibility: 4.54:1 contrast ratio on white (WCAG AA compliant)

- **Secondary Orange**: `#FF6B35` (RGB 255, 107, 53)
  - Usage: Destination markers, CTAs requiring attention, highlights
  - Conveys: Energy, action, arrival point
  - Accessibility: 3.14:1 contrast ratio on white (use for large elements only)

**Neutral Colors**
- **White**: `#FFFFFF` - Primary background, card surfaces
- **Light Gray**: `#F5F5F5` - Secondary background, hover states
- **Medium Gray**: `#E6E6E6` - Borders, disabled states, placeholder tiles
- **Dark Gray**: `#4A4A4A` - Body text (9.95:1 contrast on white)
- **Error Red**: `#B00020` - Error messages, validation failures

**Marker Colors**
- **Start Marker Green**: `#00AA00` (RGB 0, 170, 0) - 3.42:1 contrast
- **Polyline Blue**: `#0066CC` with 85% opacity - consistent with primary blue

### Typography System

**Font Stack** (using tkinter defaults with fallbacks)
- Primary: TkDefaultFont (system default sans-serif)
- Headings: TkDefaultFont, 10-11pt, bold
- Body: TkDefaultFont, 9-10pt, regular
- Labels: TkDefaultFont, 9pt, regular

**Type Scale**
- Heading 1 (Trip Summary): 11pt bold
- Heading 2 (Section titles): 10pt bold
- Body text (Instructions): 9pt regular
- Small text (Attribution, status): 8-9pt regular

### Spacing System

**Grid-Based Spacing** (8px base unit)
- Micro (4px): Between tightly related elements
- Small (8px): Between form elements, button groups
- Medium (12px): Frame padding, section separation
- Large (16px): Major component separation
- Extra Large (24px): Map viewport padding, window margins

### Interactive Element Design

**Buttons**

*Primary Button (Find Route)*
- Background: `#0066CC` (primary blue)
- Text: White, TkDefaultFont regular
- Padding: 8px horizontal, 6px vertical
- Border: None
- Hover: `#0052A3` (darker blue)
- Active: `#003D7A` (even darker)
- Disabled: `#B3B3B3` with gray text

*Secondary Button (Clear)*
- Background: `#F5F5F5` (light gray)
- Text: `#4A4A4A` (dark gray)
- Padding: 8px horizontal, 6px vertical
- Border: 1px solid `#E6E6E6`
- Hover: `#E6E6E6`
- Active: `#D9D9D9`

**Text Input Fields**
- Background: White
- Border: 1px solid `#E6E6E6`
- Focus border: 2px solid `#0066CC`
- Padding: 6px horizontal, 4px vertical
- Placeholder text: `#999999`
- Error border: 2px solid `#B00020`

**Radio Buttons**
- Unchecked: Circle outline `#E6E6E6`
- Checked: Filled circle `#0066CC` with white center dot
- Label: `#4A4A4A`, 9pt
- Hover: Background `#F5F5F5`

### Layout and Visual Hierarchy

**Window Minimum Size**: 560px × 420px

**Row Allocation** (using tkinter grid)
- Row 0: Search controls frame (fixed height ~180px)
- Row 1: Map widget (weight=1, minimum 300px)
- Row 2: Text directions (weight=1, minimum 200px)
- Row 3: Status bar (fixed height ~30px)

**Responsive Behavior**
- Window width < 560px: Enforce minimum width
- Window height < 720px: Equal allocation between map and text directions
- Window height ≥ 720px: Map receives 300px minimum, text directions get 16 lines minimum, remainder split proportionally

**Visual Hierarchy Principles**
1. **Map takes visual precedence**: Largest surface area, positioned between controls and details
2. **Controls are scannable**: Vertical rhythm with clear labels, grouped by function
3. **Status provides context**: Always visible, updates reflect current application state
4. **Directions support the map**: Complementary view, not competing for attention

## Components and Interfaces

### Map Widget Component (TkinterMapView Wrapper)

**Purpose**: Encapsulates all map rendering, interaction, and tile management logic.

**Class Structure**
```python
class MapWidget:
    """Wrapper around TkinterMapView with route visualization."""
    
    def __init__(self, parent: tk.Widget):
        self.widget = TkinterMapView(parent, corner_radius=0)
        self.widget.set_tile_server(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            max_zoom=19
        )
        self.polyline_path = None
        self.start_marker = None
        self.destination_marker = None
        
    def render_route(self, coordinates: list[tuple[float, float]]) -> None:
        """Draw route polyline and markers."""
        
    def clear_route(self) -> None:
        """Remove polyline and all markers."""
        
    def auto_fit_route(self, coordinates: list[tuple[float, float]]) -> None:
        """Adjust zoom and center to show entire route."""
        
    def reset_view(self) -> None:
        """Return to default position (0°, 0°, zoom 2)."""
```

**Public Interface**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `render_route()` | `coordinates: list[tuple[lat, lon]]` | None | Clears previous route elements, draws new polyline, places start/destination markers, auto-fits viewport |
| `clear_route()` | None | None | Removes polyline and all markers from map |
| `auto_fit_route()` | `coordinates: list[tuple[lat, lon]]` | None | Calculates bounding box and adjusts zoom/center to fit all coordinates with 24px padding |
| `reset_view()` | None | None | Pans to (0°, 0°) and sets zoom level to 2 |
| `get_widget()` | None | `TkinterMapView` | Returns the underlying tkintermapview widget for grid placement |

**State Management**
- `polyline_path`: Reference to current polyline (for removal)
- `start_marker`: Reference to start marker (for removal)
- `destination_marker`: Reference to destination marker (for removal)
- All state updates occur only on GUI thread

**Visual Properties**
- Polyline: Color `#0066CC`, width 5px, opacity 0.85
- Start marker: Circle diameter 12px, color `#00AA00`, clickable with "Starting point" popup
- Destination marker: Circle diameter 12px, color `#DD0000` (red for better contrast with orange theme), clickable with "Destination" popup
- Attribution: 10px white text with 80% opacity, positioned 5px from bottom-right, semi-transparent black background (50% opacity)

### Enhanced RouteApp Class

**Purpose**: Orchestrates the GUI, manages widget lifecycle, and coordinates between map, text directions, and backend.

**Class Structure**
```python
class RouteApp:
    """Enhanced GUI with integrated map widget."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self._closing = False
        self.map_widget: MapWidget = None
        # ... existing attributes ...
        
    def _build_input_frame(self) -> None:
        """Construct search controls with enhanced styling."""
        
    def _build_map_widget(self) -> None:
        """Create and position map widget at row 1."""
        
    def _build_result_area(self) -> None:
        """Create text directions widget at row 2."""
        
    def _build_status_bar(self) -> None:
        """Create status bar at row 3."""
        
    def _on_search(self) -> None:
        """Validate, start worker thread, update UI state."""
        
    def _on_result(self, result: dict) -> None:
        """Update map and text directions on GUI thread."""
        
    def _on_clear(self) -> None:
        """Clear all inputs, map, and text directions."""
        
    def _extract_route_geometry(self, result: dict) -> list[tuple[float, float]]:
        """Extract and validate coordinates from API result."""
```

**Threading Model**

The existing threading architecture is preserved and extended:

```python
# GUI Thread: User clicks "Find Route"
def _on_search(self) -> None:
    # Validation happens synchronously
    error = validate_inputs(self.origin_var.get(), self.destination_var.get())
    if error:
        # Show error immediately, no network call
        return
    
    # Update UI: disable button, show "Searching..." status
    self.search_button.configure(state="disabled")
    self.status_var.set("Searching...")
    
    # Clear previous map elements (synchronous, on GUI thread)
    self.map_widget.clear_route()
    
    # Start daemon worker thread
    start_route_request(
        self.root, 
        self._on_result,  # callback
        key, origin, destination, units, profile
    )

# Worker Thread: Runs run_route_request()
def run_route_request(...) -> dict:
    # Fetch route via backend/api.py
    result = api.fetch_route(...)
    # Worker does NOT touch any tkinter widgets
    # Returns result dict to be passed to callback
    return result

# GUI Thread: Callback receives result via root.after(0, ...)
def _on_result(self, result: dict) -> None:
    if self._closing:
        return  # Window destroyed, drop result
    
    # Re-enable button
    self.search_button.configure(state="normal")
    
    # Update map (only if route succeeded)
    if result.get("ok"):
        coordinates = self._extract_route_geometry(result)
        if coordinates:
            self.map_widget.render_route(coordinates)
    else:
        # Route failed, map stays clear (cleared in _on_search)
        pass
    
    # Update text directions (existing logic)
    self._render_lines(result_to_lines(result, ...))
    
    # Update status
    self.status_var.set("Done." if result.get("ok") else "Route request failed.")
```

**Key Threading Rules**
1. All tkinter widget access occurs only on GUI thread
2. Worker thread calls only `api.fetch_route()` and returns
3. `root.after(0, callback, result)` bridges worker → GUI thread
4. `_closing` flag prevents stale results from updating destroyed widgets
5. Map tile downloads happen in tkintermapview's internal threads (library handles this)

### Route Geometry Extractor

**Purpose**: Safely extract coordinate lists from API result with comprehensive error handling.

**Function Signature**
```python
def extract_route_geometry(result: dict) -> list[tuple[float, float]]:
    """Extract route coordinates from API result.
    
    Args:
        result: The dictionary returned by api.fetch_route()
        
    Returns:
        List of (latitude, longitude) tuples, or empty list if extraction fails.
        
    Notes:
        - GraphHopper returns [longitude, latitude] format
        - This function converts to [latitude, longitude] for tkintermapview
        - Invalid coordinates (lat outside ±90°, lon outside ±180°) are filtered out
        - Logs missing keys but does not raise exceptions
    """
```

**Implementation Logic**
```python
def extract_route_geometry(result: dict) -> list[tuple[float, float]]:
    try:
        # Navigate nested path: result["data"]["paths"][0]["points"]["coordinates"]
        data = result.get("data", {})
        paths = data.get("paths", [])
        if not paths:
            return []
        
        points = paths[0].get("points", {})
        coordinates = points.get("coordinates", [])
        
        # Convert [lon, lat] → [lat, lon] and validate
        valid_coords = []
        for coord in coordinates:
            if not isinstance(coord, (list, tuple)) or len(coord) < 2:
                continue
            lon, lat = float(coord[0]), float(coord[1])
            # Validate bounds
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                valid_coords.append((lat, lon))
        
        return valid_coords
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        # Log but do not crash; return empty list
        print(f"Warning: Failed to extract route geometry: {exc}")
        return []
```

### Tile Cache Manager (Handled by TkinterMapView)

**Design Note**: The tkintermapview library provides built-in tile caching and download management. Our design leverages this without reimplementation.

**Library Capabilities**
- Automatic tile download from OpenStreetMap tile server
- In-memory cache with LRU eviction
- Placeholder rendering for failed/pending tiles
- Retry logic for transient network failures

**Configuration**
```python
# In MapWidget.__init__()
self.widget.set_tile_server(
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    max_zoom=19
)
```

**Tile Server Attribution**
- OpenStreetMap requires attribution: "© OpenStreetMap contributors"
- Tkintermapview handles this automatically if configured properly
- Verification: Ensure attribution label appears at bottom-right of map widget

## Data Models

### Route Result Structure (from backend/api.py)

**Success Case**
```python
{
    "ok": True,
    "url": str,  # Contains API key, never rendered in GUI
    "data": {
        "paths": [
            {
                "distance": float,  # meters
                "time": float,      # milliseconds
                "instructions": [
                    {
                        "text": str,
                        "distance": float,  # meters
                        # ... other instruction fields
                    }
                ],
                "points": {
                    "coordinates": [
                        [longitude: float, latitude: float],  # Note: lon, lat order
                        # ... more coordinate pairs
                    ]
                }
            }
        ]
    },
    "from_name": str,  # Resolved origin name
    "to_name": str     # Resolved destination name
}
```

**Failure Case**
```python
{
    "ok": False,
    "title": str,     # User-facing error title
    "detail": str     # User-facing error description
}
```

### Map State Model

```python
@dataclass
class MapState:
    """Represents current map widget state."""
    has_route: bool = False
    coordinates: list[tuple[float, float]] = field(default_factory=list)
    center_lat: float = 0.0
    center_lon: float = 0.0
    zoom_level: int = 2
    polyline_ref: Any = None
    start_marker_ref: Any = None
    destination_marker_ref: Any = None
```

This state is managed internally by the MapWidget class and does not need explicit persistence.

### Coordinate Validation Model

```python
class CoordinateValidator:
    """Validates geographic coordinates."""
    
    LAT_MIN = -90.0
    LAT_MAX = 90.0
    LON_MIN = -180.0
    LON_MAX = 180.0
    
    @staticmethod
    def is_valid(lat: float, lon: float) -> bool:
        """Check if coordinates are within valid bounds."""
        return (
            CoordinateValidator.LAT_MIN <= lat <= CoordinateValidator.LAT_MAX
            and CoordinateValidator.LON_MIN <= lon <= CoordinateValidator.LON_MAX
        )
    
    @staticmethod
    def filter_valid(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
        """Filter list to only valid coordinates."""
        return [
            (lat, lon) for lat, lon in coords
            if CoordinateValidator.is_valid(lat, lon)
        ]
```

## Error Handling

### Error Categories and User Feedback

**Network Errors**
- **No internet connection**: Status bar shows "No network connection", map displays previous state or placeholder tiles
- **Tile download timeout**: Individual tiles show gray placeholder, map remains interactive, no modal dialogs

**API Errors**
- **Invalid API key**: Status bar shows "Invalid or unauthorized API key", text directions show setup instructions
- **Unknown location**: Status bar shows "Location not found: {query}", map clears previous route
- **Route request failed**: Status bar shows "Route request failed", map clears previous route, text directions show error detail

**Data Extraction Errors**
- **Missing "points" key**: Log warning, map displays without polyline, status shows "Done" with text directions only
- **Invalid coordinate format**: Filter out invalid coordinates, render with valid subset, log warning
- **Empty coordinate list**: Map clears route elements, text directions show summary without geometry

**UI Errors**
- **Window destroyed during request**: `_closing` flag prevents callback from touching destroyed widgets
- **Map widget initialization failure**: Graceful fallback to text-only mode with error message in status bar

### Error Handling Patterns

**Defensive Extraction**
```python
def _extract_route_geometry(self, result: dict) -> list[tuple[float, float]]:
    """Extract coordinates with comprehensive error handling."""
    if not result.get("ok"):
        return []  # Failure case, no geometry
    
    try:
        coordinates = result["data"]["paths"][0]["points"]["coordinates"]
    except (KeyError, IndexError, TypeError):
        # Missing nested key - log and return empty
        print("Warning: Route result missing 'points.coordinates' key")
        return []
    
    # Validate and convert each coordinate
    valid_coords = []
    for coord in coordinates:
        try:
            lon, lat = float(coord[0]), float(coord[1])
            if CoordinateValidator.is_valid(lat, lon):
                valid_coords.append((lat, lon))
        except (IndexError, ValueError, TypeError):
            continue  # Skip invalid coordinate, process rest
    
    return valid_coords
```

**Graceful Map Updates**
```python
def render_route(self, coordinates: list[tuple[float, float]]) -> None:
    """Render route with fallbacks for edge cases."""
    # Clear previous route (always safe)
    self.clear_route()
    
    if not coordinates:
        # No coordinates to render, map shows base tiles
        return
    
    try:
        # Draw polyline
        self.polyline_path = self.widget.set_path(
            coordinates,
            color="#0066CC",
            width=5
        )
    except Exception as exc:
        print(f"Warning: Failed to render polyline: {exc}")
        # Continue to markers even if polyline fails
    
    try:
        # Place markers
        if len(coordinates) >= 1:
            self.start_marker = self.widget.set_marker(
                coordinates[0][0], coordinates[0][1],
                text="Starting point",
                marker_color_circle="#00AA00"
            )
        if len(coordinates) >= 2:
            self.destination_marker = self.widget.set_marker(
                coordinates[-1][0], coordinates[-1][1],
                text="Destination",
                marker_color_circle="#DD0000"
            )
    except Exception as exc:
        print(f"Warning: Failed to place markers: {exc}")
        # Polyline may still be visible
    
    try:
        # Auto-fit viewport
        self.auto_fit_route(coordinates)
    except Exception as exc:
        print(f"Warning: Failed to auto-fit viewport: {exc}")
        # Route is visible at current zoom
```

**Thread-Safe Callbacks**
```python
def _on_result(self, result: dict) -> None:
    """Result callback with _closing guard."""
    # First check: window destroyed?
    if self._closing:
        return  # Drop result, do not touch any widgets
    
    # Re-enable button (safe: we checked _closing)
    self.search_button.configure(state="normal")
    
    # Wrap all updates in try-except to prevent event loop crashes
    try:
        if result.get("ok"):
            coordinates = self._extract_route_geometry(result)
            if coordinates:
                self.map_widget.render_route(coordinates)
        
        self._render_lines(result_to_lines(result, self.units_var.get(), 
                                          self.profile_var.get()),
                          error=not result.get("ok"))
        
        self.status_var.set("Done." if result.get("ok") else "Route request failed.")
    except Exception as exc:
        # Unexpected error during rendering - show in UI, never crash
        print(f"Error rendering route result: {exc}")
        self.status_var.set("Unexpected error while rendering.")
        self._render_lines([
            "Unexpected error while rendering the route:",
            f"{type(exc).__name__}: {exc}"
        ], error=True)
```

## Testing Strategy

### Unit Tests

Unit tests verify specific examples, edge cases, and error conditions. Existing test infrastructure in `tests/` will be extended.

**Test Suite: test_map_widget.py**
- `test_render_route_with_valid_coordinates`: Verify polyline and markers created
- `test_render_route_with_empty_list`: Verify no crash, map shows base tiles
- `test_render_route_with_single_coordinate`: Verify only start marker placed
- `test_clear_route_removes_all_elements`: Verify polyline and markers removed
- `test_auto_fit_calculates_correct_bounding_box`: Verify zoom and center with known coords
- `test_reset_view_returns_to_default`: Verify (0, 0) and zoom level 2

**Test Suite: test_coordinate_extraction.py**
- `test_extract_valid_coordinates`: Verify [lon, lat] → [lat, lon] conversion
- `test_extract_missing_points_key`: Verify empty list returned, no exception
- `test_extract_empty_paths_list`: Verify empty list returned
- `test_extract_filters_invalid_latitudes`: Verify lat outside ±90° excluded
- `test_extract_filters_invalid_longitudes`: Verify lon outside ±180° excluded
- `test_extract_handles_malformed_coordinates`: Verify non-numeric coords skipped

**Test Suite: test_gui_integration.py** (extends existing test_gui_logic.py)
- `test_on_search_clears_previous_route`: Verify map cleared before request
- `test_on_result_renders_map_with_valid_geometry`: Verify map updated on success
- `test_on_result_leaves_map_clear_on_failure`: Verify map not updated on API error
- `test_on_clear_resets_map_to_default_view`: Verify map returns to (0, 0), zoom 2
- `test_closing_flag_prevents_stale_updates`: Verify _closing drops result

**Test Suite: test_error_handling.py**
- `test_network_error_shows_friendly_message`: Verify status bar and text widget
- `test_invalid_key_shows_setup_instructions`: Verify config.SETUP_MESSAGE rendered
- `test_missing_coordinates_renders_text_only`: Verify text directions work without map
- `test_tile_download_failure_shows_placeholder`: Verify map remains interactive

### Integration Tests

Integration tests verify component interaction and end-to-end behavior.

**Test Scenarios**
1. **Complete route request flow**: User enters locations → map renders → text directions update → status shows "Done"
2. **Window resize behavior**: Map and text directions adjust proportionally, minimum sizes enforced
3. **Multiple sequential requests**: Previous route clears, new route renders correctly
4. **Request while previous request pending**: Button disabled, status shows "Searching...", new request queued
5. **Close window during request**: No crashes, _closing flag prevents updates
6. **Missing API key scenario**: Setup message shown, button click does not start request

### Visual Regression Tests (Manual)

**Checklist for Manual Testing**
- [ ] Map tiles load and display correctly at various zoom levels
- [ ] Route polyline renders with correct color (#0066CC) and 5px width
- [ ] Start marker appears green (#00AA00) at first coordinate
- [ ] Destination marker appears red (#DD0000) at last coordinate
- [ ] Clicking markers shows popup labels ("Starting point", "Destination")
- [ ] Pan gesture (mouse drag) translates map smoothly
- [ ] Zoom gesture (mouse wheel) changes zoom level incrementally
- [ ] Attribution text "© OpenStreetMap contributors" visible at bottom-right
- [ ] Window resize maintains map aspect ratio and minimum sizes
- [ ] Text directions remain scrollable and readable
- [ ] Status bar updates reflect current operation state
- [ ] Error states display in red with clear messaging

**Cross-Platform Testing**
- Windows 10/11: Verify tkinter rendering, mouse wheel zoom direction
- macOS: Verify retina display scaling, trackpad gestures (if supported)
- Linux (Ubuntu/Fedora): Verify X11/Wayland compatibility, font rendering

### Performance Tests

**Metrics to Monitor**
- Map render time: < 200ms from callback to visible polyline/markers
- Tile download time: < 10 seconds per tile (controlled by timeout)
- Memory usage: < 100MB for 500 cached tiles
- GUI responsiveness: No frame drops during pan/zoom at 30fps minimum

**Load Testing Scenarios**
- Route with 1000+ coordinate points: Should render smoothly
- Rapid zoom in/out: Should queue tile requests without blocking UI
- Window resize during route rendering: Should complete render at new size

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptance Criteria Testing Prework

#### Requirement 1: Embed Map Widget in GUI Window

1.1 THE GUI_Application SHALL embed a Map_Widget as a child of the main window's grid layout at row position 1, between the search controls frame (row 0) and the text directions frame (row 2)
  **Thoughts**: This is testing the structural setup of the GUI layout. We can verify this by checking that the map widget is correctly positioned in the grid after initialization.
  **Classification**: EXAMPLE
  **Test Strategy**: Single test to verify map widget is at row=1 in grid layout

1.2 WHEN the user resizes the window horizontally, THE Map_Widget SHALL adjust its width to match the window width minus 24 pixels (12-pixel padding on each side)
  **Thoughts**: This is testing responsive behavior that should hold for any window width. We can generate random window widths and verify the map widget width calculation.
  **Classification**: PROPERTY
  **Test Strategy**: Generate various window widths, verify map width = window_width - 24

1.3 WHEN the user resizes the window vertically, THE Map_Widget SHALL adjust its height while maintaining a minimum height of 300 pixels and allocating remaining space proportionally between itself and the text directions widget
  **Thoughts**: This is a universal property about height allocation that should hold for any window height >= minimum.
  **Classification**: PROPERTY
  **Test Strategy**: Generate window heights, verify map height >= 300px and proportional allocation

1.4 THE Map_Widget SHALL measure at least 400 pixels wide and 300 pixels tall when the window is at its minimum size of 560x420 pixels
  **Thoughts**: This is testing a specific boundary condition at minimum window size.
  **Classification**: EDGE_CASE
  **Test Strategy**: Verify dimensions at exactly 560x420 window size

1.5 WHEN the GUI_Application initializes the Map_Widget before any route request, THE Map_Widget SHALL display base map tiles centered at latitude 0°, longitude 0° with zoom level 2
  **Thoughts**: This is testing initial state setup, which is deterministic and happens once per widget lifetime.
  **Classification**: EXAMPLE
  **Test Strategy**: Single test verifying initial position and zoom after widget creation

1.6 WHEN the Tile_Provider fails to load tiles during initialization, THE Map_Widget SHALL display a light gray placeholder background and remain interactive for pan and zoom operations
  **Thoughts**: This is testing tile loading failure behavior, which is infrastructure-related.
  **Classification**: INTEGRATION
  **Test Strategy**: Mock tile server failure, verify placeholder display and interaction remain functional

1.7 WHEN the window size is less than 560x420 pixels, THE GUI_Application SHALL enforce the minimum dimensions and prevent further shrinking
  **Thoughts**: This is testing boundary enforcement at minimum dimensions.
  **Classification**: EDGE_CASE
  **Test Strategy**: Attempt to resize below 560x420, verify dimensions clamped to minimum

#### Requirement 2: Display Route Geometry on Map

2.1 WHEN a route request completes successfully, THE GUI_Application SHALL extract Route_Geometry as the list at `result["data"]["paths"][0]["points"]["coordinates"]`
  **Thoughts**: This is testing data extraction logic that should work for any valid route result structure.
  **Classification**: PROPERTY
  **Test Strategy**: Generate random route results with valid structure, verify extraction succeeds

2.2 IF the extraction fails because the "points" key is missing, THEN THE GUI_Application SHALL log the absence and leave the Map_Widget displaying only base tiles without a polyline
  **Thoughts**: This is testing error handling for missing data, which should behave consistently.
  **Classification**: PROPERTY
  **Test Strategy**: Generate route results with various missing keys, verify graceful handling

2.3 WHEN Route_Geometry is a non-empty list, THE Map_Widget SHALL render Route_Geometry as a continuous polyline connecting each coordinate in sequence
  **Thoughts**: This is a universal property—any non-empty coordinate list should render as a polyline.
  **Classification**: PROPERTY
  **Test Strategy**: Generate coordinate lists of varying lengths, verify polyline rendered

2.4 THE polyline SHALL use color #0066CC (blue), stroke width 5 pixels, and opacity 0.85
  **Thoughts**: This is testing visual styling properties that should be constant.
  **Classification**: PROPERTY
  **Test Strategy**: For any rendered polyline, verify style attributes match specification

2.5 WHEN Route_Geometry contains zero coordinates, THE Map_Widget SHALL display the base map without rendering a polyline
  **Thoughts**: This is testing an edge case with empty input.
  **Classification**: EDGE_CASE
  **Test Strategy**: Pass empty coordinate list, verify no polyline rendered

#### Requirement 3: Display Start and Destination Markers

3.1 WHEN a route is displayed and Route_Geometry contains at least one coordinate, THE Map_Widget SHALL place a Marker at the first coordinate of Route_Geometry
  **Thoughts**: This is a universal property about marker placement that should hold for any coordinate list with at least one element.
  **Classification**: PROPERTY
  **Test Strategy**: Generate coordinate lists with length >= 1, verify start marker placed at first coordinate

3.2 WHEN a route is displayed and Route_Geometry contains at least two coordinates, THE Map_Widget SHALL place a Marker at the last coordinate of Route_Geometry
  **Thoughts**: This is a universal property about marker placement for lists with 2+ elements.
  **Classification**: PROPERTY
  **Test Strategy**: Generate coordinate lists with length >= 2, verify destination marker placed at last coordinate

3.3 WHEN Route_Geometry contains only one coordinate, THE Map_Widget SHALL place only one Marker at that coordinate using the start Marker style
  **Thoughts**: This is testing a specific edge case with single-element list.
  **Classification**: EDGE_CASE
  **Test Strategy**: Pass single-coordinate list, verify only start marker placed

3.4 THE start Marker SHALL use a green icon (RGB #00AA00) with a circle shape of 12-pixel diameter
  **Thoughts**: This is testing visual styling that should be constant for all start markers.
  **Classification**: PROPERTY
  **Test Strategy**: For any start marker, verify color and size attributes

3.5 THE destination Marker SHALL use a red icon (RGB #DD0000) with a circle shape of 12-pixel diameter
  **Thoughts**: This is testing visual styling that should be constant for all destination markers.
  **Classification**: PROPERTY
  **Test Strategy**: For any destination marker, verify color and size attributes

3.6 WHEN the user clicks a start Marker, THE Map_Widget SHALL display a popup label containing the text "Starting point" positioned 20 pixels above the Marker
  **Thoughts**: This is UI interaction behavior that should work consistently for any start marker.
  **Classification**: PROPERTY
  **Test Strategy**: Generate various start marker positions, click each, verify popup text and position

3.7 WHEN the user clicks a destination Marker, THE Map_Widget SHALL display a popup label containing the text "Destination" positioned 20 pixels above the Marker
  **Thoughts**: This is UI interaction behavior that should work consistently for any destination marker.
  **Classification**: PROPERTY
  **Test Strategy**: Generate various destination marker positions, click each, verify popup text and position

#### Requirement 4: Auto-Fit Map Viewport to Route

4.1 WHEN a route is displayed and Route_Geometry contains at least two coordinates, THE GUI_Application SHALL compute the Bounding_Box as the minimum latitude, maximum latitude, minimum longitude, and maximum longitude spanning all coordinates in Route_Geometry
  **Thoughts**: This is a geometric calculation that should work for any coordinate set with 2+ elements.
  **Classification**: PROPERTY
  **Test Strategy**: Generate random coordinate lists, verify bounding box calculation correctness

4.2 WHEN the Bounding_Box is computed, THE Map_Widget SHALL adjust the Zoom_Level to the largest integer zoom value (between 1 and 19) such that the Bounding_Box fits within the visible Viewport
  **Thoughts**: This is a universal property about zoom calculation based on bounding box and viewport size.
  **Classification**: PROPERTY
  **Test Strategy**: Generate bounding boxes and viewport sizes, verify zoom level calculation

4.3 WHEN the Zoom_Level is determined, THE Map_Widget SHALL center the Viewport on the geographic midpoint of the Bounding_Box
  **Thoughts**: This is a universal property about centering calculation.
  **Classification**: PROPERTY
  **Test Strategy**: For any bounding box, verify viewport center equals midpoint

4.4 WHEN adjusting the Viewport, THE Map_Widget SHALL add 24 pixels of padding on each edge (top, bottom, left, right) between the Bounding_Box and the Viewport border
  **Thoughts**: This is a universal property about padding calculation.
  **Classification**: PROPERTY
  **Test Strategy**: Verify bounding box edges are 24px from viewport edges for any route

4.5 WHEN a user requests a new route while a previous route is displayed, THE Map_Widget SHALL compute and apply the new Bounding_Box for the new route within 200 milliseconds of receiving the route data
  **Thoughts**: This is a performance requirement that should hold for any route transition.
  **Classification**: PROPERTY
  **Test Strategy**: Generate random route pairs, measure viewport update time, verify < 200ms

4.6 WHEN Route_Geometry contains fewer than two coordinates, THE Map_Widget SHALL center the Viewport on the single coordinate (if present) at zoom level 15
  **Thoughts**: This is testing edge case behavior with 0 or 1 coordinates.
  **Classification**: EDGE_CASE
  **Test Strategy**: Test with 0 and 1 coordinate, verify centering and zoom level 15

4.7 WHEN Route_Geometry contains invalid coordinates (latitude outside ±90° or longitude outside ±180°), THE Map_Widget SHALL exclude those coordinates from the Bounding_Box calculation
  **Thoughts**: This is testing input validation that should filter out-of-bounds coordinates consistently.
  **Classification**: PROPERTY
  **Test Strategy**: Generate coordinate lists with some invalid entries, verify valid subset used for bounding box

#### Requirement 5: Support Map Pan Interaction

5.1 WHEN the user presses the left mouse button while the cursor is positioned over the Map_Widget, THE Map_Widget SHALL record the cursor's pixel coordinates as the pan origin
  **Thoughts**: This is UI interaction behavior that should work at any cursor position over the widget.
  **Classification**: PROPERTY
  **Test Strategy**: Generate random cursor positions, verify pan origin recorded on mouse down

5.2 WHILE the left mouse button remains pressed, THE Map_Widget SHALL translate the map content by the vector difference between the current cursor position and the pan origin, updating at least 30 times per second
  **Thoughts**: This is testing continuous interaction behavior that should work for any drag gesture.
  **Classification**: PROPERTY
  **Test Strategy**: Simulate drag gestures with various distances/directions, verify translation and frame rate

5.3 WHEN the left mouse button is released or the cursor exits the Map_Widget bounds, THE Map_Widget SHALL stop translating the map content and finalize the current Viewport position
  **Thoughts**: This is UI interaction termination that should work consistently.
  **Classification**: PROPERTY
  **Test Strategy**: For any drag gesture, verify translation stops on mouse up or cursor exit

5.4 WHEN the Viewport position changes during a pan operation, THE Map_Widget SHALL identify newly visible tile coordinates and request any tiles not already cached
  **Thoughts**: This is infrastructure behavior (tile loading) that should work during any pan.
  **Classification**: INTEGRATION
  **Test Strategy**: Pan to reveal new area, verify tile requests issued for uncached tiles

5.5 WHEN tile loading fails during a pan operation, THE Map_Widget SHALL continue to respond to pan gestures without interruption
  **Thoughts**: This is testing resilience during infrastructure failures.
  **Classification**: INTEGRATION
  **Test Strategy**: Mock tile failures during pan, verify pan gestures still functional

#### Requirement 6: Support Map Zoom Interaction

6.1 WHEN the user scrolls the mouse wheel forward (away from the user) over the Map_Widget, THE Map_Widget SHALL increment the Zoom_Level by 1 integer step
  **Thoughts**: This is UI interaction behavior that should work at any current zoom level.
  **Classification**: PROPERTY
  **Test Strategy**: Test wheel-up at various zoom levels, verify increment by 1

6.2 WHEN the user scrolls the mouse wheel backward (toward the user) over the Map_Widget, THE Map_Widget SHALL decrement the Zoom_Level by 1 integer step
  **Thoughts**: This is UI interaction behavior that should work at any current zoom level.
  **Classification**: PROPERTY
  **Test Strategy**: Test wheel-down at various zoom levels, verify decrement by 1

6.3 THE Map_Widget SHALL clamp Zoom_Level to the inclusive range [1, 19], such that incrementing at level 19 leaves Zoom_Level unchanged, and decrementing at level 1 leaves Zoom_Level unchanged
  **Thoughts**: This is boundary clamping behavior that should work at zoom limits.
  **Classification**: EDGE_CASE
  **Test Strategy**: Test zoom up at level 19 and zoom down at level 1, verify no change

6.4 WHEN Zoom_Level changes, THE Map_Widget SHALL request new tiles with zoom coordinate matching the new Zoom_Level value and re-render Route_Geometry at the new scale
  **Thoughts**: This is infrastructure behavior (tile loading) combined with geometry re-rendering.
  **Classification**: INTEGRATION
  **Test Strategy**: Change zoom level, verify new tiles requested and polyline re-rendered

6.5 WHEN the Route_Geometry polyline is displayed and the user changes Zoom_Level, THE Map_Widget SHALL preserve the polyline's color (#0066CC), stroke width (5 pixels), and opacity (0.85) at the new zoom
  **Thoughts**: This is a universal property about style preservation across zoom changes.
  **Classification**: PROPERTY
  **Test Strategy**: For any zoom change with polyline visible, verify style attributes unchanged

6.6 WHEN tile loading fails after a zoom operation, THE Map_Widget SHALL display placeholder rectangles for missing tiles and continue to respond to subsequent zoom operations
  **Thoughts**: This is testing resilience during infrastructure failures.
  **Classification**: INTEGRATION
  **Test Strategy**: Mock tile failures after zoom, verify placeholders shown and zoom still functional

#### Requirement 7: Fetch and Cache Map Tiles

7.1-7.10 All tile fetching and caching criteria
  **Thoughts**: These are infrastructure operations handled by the tkintermapview library. We are not testing the library itself, but rather that our integration configures it correctly.
  **Classification**: INTEGRATION
  **Test Strategy**: Mock tile server, verify requests sent with correct URLs, cache behavior through observation

#### Requirement 8: Handle Tile Download Failures Gracefully

8.1-8.6 All tile failure handling criteria
  **Thoughts**: These are infrastructure resilience tests—external service failures should not break interaction.
  **Classification**: INTEGRATION
  **Test Strategy**: Mock various tile server failures, verify placeholders and continued interaction

#### Requirement 9: Preserve Text Directions Alongside Map

9.1 WHEN a successful route request completes, THE GUI_Application SHALL display both the Map_Widget and the text directions widget in a vertical layout with the Map_Widget at grid row 1 and the text directions widget at grid row 2
  **Thoughts**: This is testing layout structure that should be consistent for any successful route.
  **Classification**: EXAMPLE
  **Test Strategy**: Single test verifying both widgets present in correct rows after route success

9.2 THE text directions widget SHALL remain scrollable via its attached vertical scrollbar after the Map_Widget is added
  **Thoughts**: This is testing UI component functionality that should persist.
  **Classification**: EXAMPLE
  **Test Strategy**: Verify scrollbar functional after map widget initialization

9.3 THE text directions widget SHALL display the same numbered turn-by-turn instructions with distance values as the current implementation without modification
  **Thoughts**: This is testing preservation of existing functionality.
  **Classification**: PROPERTY
  **Test Strategy**: For any route result, verify text directions match expected format from result_to_lines()

9.4 WHEN the window height is less than 720 pixels (insufficient to show both the Map_Widget at 300 pixels and the text directions widget at 16 lines of text), THE GUI_Application SHALL allocate the available height equally between the Map_Widget and the text directions widget, with each receiving independent scrollbars if their content exceeds their allocated height
  **Thoughts**: This is testing responsive layout behavior at constrained window sizes.
  **Classification**: PROPERTY
  **Test Strategy**: Test with various window heights < 720px, verify equal allocation and scrollbar presence

#### Requirement 10: Clear Map When Route Request Fails

10.1-10.7 All map clearing criteria on failure
  **Thoughts**: These are testing error handling behavior—map should clear consistently on any failure type.
  **Classification**: PROPERTY (for each failure category)
  **Test Strategy**: Generate various failure scenarios, verify map clears polyline/markers but retains base tiles

#### Requirement 11: Attribute Map Tile Provider

11.1-11.6 All attribution display criteria
  **Thoughts**: These are testing UI element positioning and styling that should be constant.
  **Classification**: EXAMPLE (positioning), PROPERTY (persistence during interaction)
  **Test Strategy**: Verify attribution present with correct position/style; verify position fixed during pan/zoom

#### Requirement 12: Reuse Existing Route Data Structure

12.1-12.6 All data structure extraction criteria
  **Thoughts**: These are testing data extraction and coordinate conversion logic.
  **Classification**: PROPERTY (for extraction and conversion logic)
  **Test Strategy**: Generate route results with various structures, verify extraction and [lon,lat]→[lat,lon] conversion

#### Requirement 13: Integrate Map Library with Minimal Dependencies

13.1-13.5 All library integration criteria
  **Thoughts**: These are infrastructure setup tests—library imports and cross-platform compatibility.
  **Classification**: INTEGRATION / SMOKE
  **Test Strategy**: Verify import succeeds, widget instantiates; test on Windows/macOS/Linux

#### Requirement 14: Maintain Thread Safety for Background Requests

14.1-14.6 All thread safety criteria
  **Thoughts**: These are testing concurrency behavior—thread boundaries and callback safety.
  **Classification**: PROPERTY (for callback execution), INTEGRATION (for threading behavior)
  **Test Strategy**: Simulate concurrent scenarios (close during request, multiple requests), verify thread safety

#### Requirement 15: Provide Visual Feedback During Route Requests

15.1-15.6 All visual feedback criteria
  **Thoughts**: These are testing UI state transitions and timing requirements.
  **Classification**: PROPERTY (for state transitions), PERFORMANCE (for timing)
  **Test Strategy**: For any route request, verify UI state progression; measure timing compliance

### Reflection on Properties

After reviewing all testable criteria, the following properties emerge as the core universal behaviors that warrant property-based testing:

**Geometric Properties** (Requirements 1-4)
- Window resize calculations (width/height allocation)
- Bounding box calculation from coordinates
- Zoom level calculation from bounding box
- Coordinate validation and filtering

**Interaction Properties** (Requirements 5-6)
- Pan translation vector calculation
- Zoom level clamping and increment/decrement
- Style preservation across zoom changes

**Data Properties** (Requirements 2, 10, 12)
- Coordinate extraction from nested structures
- Coordinate format conversion [lon, lat] → [lat, lon]
- Graceful handling of missing/invalid data
- Map clearing on failure scenarios

**UI State Properties** (Requirements 9, 14, 15)
- Layout allocation under varying window sizes
- Thread-safe callback execution
- State transition consistency (idle → searching → done → error)

**Redundancy Identified:**
- Requirements 2.3 and 2.4 (polyline rendering and styling) can be combined into one property: "For any non-empty coordinate list, polyline is rendered with correct style"
- Requirements 3.1 and 3.2 (start and destination markers) can be combined into one property with conditional logic based on coordinate count
- Requirements 4.2 and 4.3 (zoom calculation and centering) are both part of the auto-fit algorithm and can be tested together
- Requirements 5.1, 5.2, 5.3 (pan interaction phases) are sequential parts of one pan gesture property
- Requirements 6.1, 6.2, 6.3 (zoom interaction) can be combined into one zoom gesture property with boundary testing

After consolidation, we proceed to write correctness properties.

### Property 1: Window Resize Maintains Layout Constraints

*For any* window size (width, height) where width ≥ 560 and height ≥ 420, the map widget width SHALL equal window width minus 24 pixels, and the map widget height SHALL be at least 300 pixels with remaining height allocated proportionally to text directions widget.

**Validates: Requirements 1.2, 1.3, 1.4, 9.4**

### Property 2: Route Polyline Renders with Correct Style

*For any* non-empty list of valid coordinates, when rendered as a polyline, the polyline SHALL use color #0066CC, stroke width 5 pixels, and opacity 0.85, connecting all coordinates in sequence.

**Validates: Requirements 2.3, 2.4**

### Property 3: Marker Placement Follows Coordinate Count Rules

*For any* coordinate list with length N ≥ 1:
- If N = 1, a single start marker SHALL be placed at coordinate 0
- If N ≥ 2, a start marker SHALL be placed at coordinate 0 and a destination marker SHALL be placed at coordinate N-1
- Start markers SHALL use color #00AA00 with 12px diameter
- Destination markers SHALL use color #DD0000 with 12px diameter

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 4: Marker Click Displays Correct Popup

*For any* start marker, clicking it SHALL display a popup with text "Starting point" positioned 20 pixels above the marker. *For any* destination marker, clicking it SHALL display a popup with text "Destination" positioned 20 pixels above the marker.

**Validates: Requirements 3.6, 3.7**

### Property 5: Bounding Box Calculation Spans All Valid Coordinates

*For any* coordinate list with at least 2 valid coordinates (latitude in [-90, 90], longitude in [-180, 180]), the bounding box SHALL be calculated as (min_lat, max_lat, min_lon, max_lon) spanning all valid coordinates, excluding any invalid coordinates.

**Validates: Requirements 4.1, 4.7**

### Property 6: Auto-Fit Centers and Zooms to Bounding Box

*For any* bounding box and viewport size, the map SHALL:
- Set zoom level to the maximum integer in [1, 19] such that the bounding box fits within the viewport
- Center the viewport on the geographic midpoint of the bounding box
- Add 24 pixels of padding on each edge between bounding box and viewport border

**Validates: Requirements 4.2, 4.3, 4.4**

### Property 7: Route Transition Completes Within Time Budget

*For any* pair of routes (previous, new), when transitioning from displaying the previous route to displaying the new route, the viewport SHALL compute and apply the new bounding box within 200 milliseconds of receiving the new route data.

**Validates: Requirements 4.5**

### Property 8: Pan Gesture Translates Map by Cursor Delta

*For any* pan gesture (mouse down at point A, drag to point B, mouse up), the map content SHALL translate by the vector (B - A), updating the viewport position continuously at ≥30fps, and finalizing position on mouse up or cursor exit.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 9: Zoom Gesture Changes Level by One Step with Clamping

*For any* current zoom level Z in [1, 19]:
- Mouse wheel forward SHALL set zoom to min(Z + 1, 19)
- Mouse wheel backward SHALL set zoom to max(Z - 1, 1)
- Style of any visible polyline SHALL remain color #0066CC, width 5px, opacity 0.85 after zoom change

**Validates: Requirements 6.1, 6.2, 6.3, 6.5**

### Property 10: Coordinate Extraction Converts Format Correctly

*For any* API result containing nested path `result["data"]["paths"][0]["points"]["coordinates"]` as a list of [longitude, latitude] pairs, the extraction function SHALL return a list of [latitude, longitude] tuples, filtering out any pairs that are not numeric or have coordinates outside valid bounds.

**Validates: Requirements 12.1, 12.4, 12.5, 12.6**

### Property 11: Missing Data Keys Return Empty Geometry

*For any* API result where any key in the path `["data"]["paths"][0]["points"]["coordinates"]` is missing or `paths` is empty, the extraction function SHALL return an empty list without raising an exception.

**Validates: Requirements 2.2, 12.2, 12.3**

### Property 12: Map Clears Route Elements on Any Failure

*For any* failure scenario (validation error, HTTP error, timeout, invalid response), the map widget SHALL remove all polyline and marker elements while preserving base tiles and interaction capability, and the status bar SHALL display an appropriate error message.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

### Property 13: Clear Action Resets Map to Default State

*For any* map state (with or without route displayed), clicking the Clear button SHALL remove all route elements, reset viewport to (0°, 0°) with zoom level 2, clear input fields, and set status to default message.

**Validates: Requirements 10.6**

### Property 14: Text Directions Match Formatted Route

*For any* successful route result, the text directions widget SHALL display content identical to the output of `result_to_lines(result, units, profile)`, preserving all summary fields and numbered turn-by-turn instructions.

**Validates: Requirements 9.3**

### Property 15: Thread-Safe Callback Execution

*For any* route request initiated from GUI thread:
- Route fetching SHALL execute on daemon worker thread
- Worker SHALL call only `api.fetch_route()` and `root.after(0, callback, result)`
- Callback SHALL execute on GUI thread
- If `_closing` flag is True, callback SHALL skip all widget updates without error
- All map widget access SHALL occur only on GUI thread

**Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6**

### Property 16: Visual Feedback State Transitions

*For any* route request flow:
- Clicking "Find Route" SHALL clear previous map elements within 50ms and set status to "Searching..."
- Route result arrival SHALL render new route within 100ms of callback
- Completion SHALL update status to "Done." or error message within 100ms
- Timeout after 30 seconds SHALL update status to "The request timed out"

**Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5, 15.6**

## Implementation Checklist

### Phase 1: Foundation (Map Widget Integration)

- [ ] Add `tkintermapview==1.29` to `requirements.txt`
- [ ] Create `MapWidget` class wrapping TkinterMapView
- [ ] Implement `render_route()` method
- [ ] Implement `clear_route()` method
- [ ] Implement `auto_fit_route()` method with bounding box calculation
- [ ] Implement `reset_view()` method
- [ ] Configure OpenStreetMap tile server with attribution

### Phase 2: GUI Integration

- [ ] Modify `RouteApp.__init__()` to instantiate MapWidget at row 1
- [ ] Update grid row weights for map (row 1, weight=1) and text (row 2, weight=1)
- [ ] Implement `_extract_route_geometry()` with coordinate validation
- [ ] Implement coordinate format conversion [lon, lat] → [lat, lon]
- [ ] Update `_on_search()` to clear map before starting request
- [ ] Update `_on_result()` to call `map_widget.render_route()` on success
- [ ] Update `_on_clear()` to call `map_widget.reset_view()`
- [ ] Test window resize behavior with minimum size enforcement

### Phase 3: Error Handling

- [ ] Implement defensive extraction with try-except blocks
- [ ] Add logging for missing "points" key
- [ ] Test empty coordinate list handling
- [ ] Test invalid coordinate filtering (lat/lon out of bounds)
- [ ] Test _closing flag prevents stale updates
- [ ] Test tile download failures show placeholders

### Phase 4: UI Polish

- [ ] Apply color palette to buttons (`#0066CC` for "Find Route")
- [ ] Style input fields with focus state (`#0066CC` border)
- [ ] Verify marker colors (green start, red destination)
- [ ] Verify polyline color and width
- [ ] Verify attribution text visibility
- [ ] Test status bar messages for all states
- [ ] Add subtle shadows/borders for visual depth (optional enhancement)

### Phase 5: Testing

- [ ] Write unit tests for `extract_route_geometry()`
- [ ] Write unit tests for `MapWidget` methods
- [ ] Write unit tests for coordinate validation
- [ ] Extend `tests/test_gui_logic.py` with map integration tests
- [ ] Write integration tests for threading behavior
- [ ] Perform manual visual regression testing on Windows
- [ ] Perform manual testing on macOS (if available)
- [ ] Perform manual testing on Linux (if available)
- [ ] Run full test suite: `py -m pytest tests -v`

### Phase 6: Documentation

- [ ] Update `ARCHITECTURE.md` with map widget section
- [ ] Update `README.md` with map feature description
- [ ] Add screenshots showing map interface (optional)
- [ ] Document color palette in comments
- [ ] Add inline comments explaining bounding box algorithm
- [ ] Update docstrings for modified methods

### Phase 7: Performance Validation

- [ ] Measure map render time (should be < 200ms)
- [ ] Test route with 1000+ coordinates
- [ ] Test rapid zoom in/out
- [ ] Monitor memory usage during prolonged use
- [ ] Test window resize during route rendering
- [ ] Verify 30fps pan gesture smoothness

## Deployment Notes

### Dependencies

Add to `requirements.txt`:
```
tkintermapview==1.29
```

Existing dependencies remain unchanged:
- `requests` (API calls)
- `rich` (CLI display)
- `flask` (web frontend)
- `pytest` (testing)

### Installation Instructions

Update `README.md` installation section:
```bash
py -m pip install -r requirements.txt
```

### Platform-Specific Considerations

**Windows**
- tkinter ships with python.org installer
- Verify with: `py -c "import tkinter; print(tkinter.TkVersion)"`
- Mouse wheel direction: forward = zoom in

**macOS**
- tkinter may require separate installation: `brew install python-tk`
- Test on both Intel and Apple Silicon
- Trackpad gestures: pinch-to-zoom may not work with tkintermapview

**Linux**
- tkinter package: `sudo apt-get install python3-tk` (Ubuntu/Debian)
- Test on both X11 and Wayland
- Verify font rendering in map attribution

### Known Limitations

1. **Offline Mode**: Map tiles require internet connection; offline fallback not implemented
2. **Tile Server Rate Limits**: OpenStreetMap tile server has usage policies; excessive requests may be throttled
3. **Memory Usage**: 500-tile cache limit may be insufficient for extensive pan/zoom sessions
4. **Trackpad Gestures**: Only mouse wheel zoom supported; trackpad pinch-to-zoom not implemented
5. **Retina/HiDPI Displays**: tkintermapview may render tiles at non-native resolution on high-DPI displays
6. **Accessibility**: Keyboard navigation for map not implemented; screen reader support limited

### Future Enhancements

1. **Offline Tile Caching**: Persist tiles to disk for offline use
2. **Alternative Tile Providers**: Support Mapbox, Google Maps (requires API keys)
3. **Route Comparison**: Display multiple routes with different colors
4. **Elevation Profile**: Show elevation graph below map for routes with terrain data
5. **Traffic Layer**: Overlay real-time traffic data (requires additional API)
6. **Custom Markers**: Allow users to add waypoints by clicking map
7. **Export Map**: Save map view as PNG image
8. **Dark Mode**: Alternative color scheme for map tiles and UI
9. **Accessibility**: Keyboard shortcuts for zoom/pan, screen reader announcements for route updates
10. **Mobile Version**: Responsive web version with touch gestures (separate feature)
