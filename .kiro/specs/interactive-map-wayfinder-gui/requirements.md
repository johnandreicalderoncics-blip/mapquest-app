# Requirements Document

## Introduction

The Interactive Map Wayfinder GUI feature adds visual route presentation to the existing tkinter desktop interface. Users currently see turn-by-turn directions as plain text in a scrollable widget. This feature embeds an interactive map displaying the route geometry, start and destination markers, and supports pan/zoom interaction. The map visualization reuses route data already fetched from the GraphHopper API, maintaining the existing backend contract and presentation-neutral formatting layers.

## Glossary

- **GUI_Application**: The existing tkinter desktop application (`gui.py`)
- **Map_Widget**: The embedded tkinter canvas displaying the interactive map
- **Route_Geometry**: The sequence of latitude/longitude coordinates defining the path
- **Tile_Provider**: External map tile service providing base layer images (OpenStreetMap)
- **Viewport**: The visible rectangular region of the map displayed to the user
- **Zoom_Level**: Integer representing map scale (higher = more detail)
- **Marker**: Visual indicator on the map representing a point of interest
- **Bounding_Box**: Geographic rectangle encompassing all route points

## Requirements

### Requirement 1: Embed Map Widget in GUI Window

**User Story:** As a desktop user, I want to see an interactive map in the GUI window, so that I can visualize routes spatially.

#### Acceptance Criteria

1. THE GUI_Application SHALL embed a Map_Widget as a child of the main window's grid layout at row position 1, between the search controls frame (row 0) and the text directions frame (row 2)
2. WHEN the user resizes the window horizontally, THE Map_Widget SHALL adjust its width to match the window width minus 24 pixels (12-pixel padding on each side)
3. WHEN the user resizes the window vertically, THE Map_Widget SHALL adjust its height while maintaining a minimum height of 300 pixels and allocating remaining space proportionally between itself and the text directions widget
4. THE Map_Widget SHALL measure at least 400 pixels wide and 300 pixels tall when the window is at its minimum size of 560x420 pixels
5. WHEN the GUI_Application initializes the Map_Widget before any route request, THE Map_Widget SHALL display base map tiles centered at latitude 0°, longitude 0° with zoom level 2
6. WHEN the Tile_Provider fails to load tiles during initialization, THE Map_Widget SHALL display a light gray placeholder background and remain interactive for pan and zoom operations
7. WHEN the window size is less than 560x420 pixels, THE GUI_Application SHALL enforce the minimum dimensions and prevent further shrinking

### Requirement 2: Display Route Geometry on Map

**User Story:** As a desktop user, I want the fetched route drawn on the map, so that I can see the path I will take.

#### Acceptance Criteria

1. WHEN a route request completes successfully, THE GUI_Application SHALL extract Route_Geometry as the list at `result["data"]["paths"][0]["points"]["coordinates"]`
2. IF the extraction fails because the "points" key is missing, THEN THE GUI_Application SHALL log the absence and leave the Map_Widget displaying only base tiles without a polyline
3. WHEN Route_Geometry is a non-empty list, THE Map_Widget SHALL render Route_Geometry as a continuous polyline connecting each coordinate in sequence
4. THE polyline SHALL use color #0066CC (blue), stroke width 5 pixels, and opacity 0.85
5. WHEN Route_Geometry contains zero coordinates, THE Map_Widget SHALL display the base map without rendering a polyline

### Requirement 3: Display Start and Destination Markers

**User Story:** As a desktop user, I want to see where my route starts and ends on the map, so that I can confirm the correct locations.

#### Acceptance Criteria

1. WHEN a route is displayed and Route_Geometry contains at least one coordinate, THE Map_Widget SHALL place a Marker at the first coordinate of Route_Geometry
2. WHEN a route is displayed and Route_Geometry contains at least two coordinates, THE Map_Widget SHALL place a Marker at the last coordinate of Route_Geometry
3. WHEN Route_Geometry contains only one coordinate, THE Map_Widget SHALL place only one Marker at that coordinate using the start Marker style
4. THE start Marker SHALL use a green icon (RGB #00AA00) with a circle shape of 12-pixel diameter
5. THE destination Marker SHALL use a red icon (RGB #DD0000) with a circle shape of 12-pixel diameter
6. WHEN the user clicks a start Marker, THE Map_Widget SHALL display a popup label containing the text "Starting point" positioned 20 pixels above the Marker
7. WHEN the user clicks a destination Marker, THE Map_Widget SHALL display a popup label containing the text "Destination" positioned 20 pixels above the Marker

### Requirement 4: Auto-Fit Map Viewport to Route

**User Story:** As a desktop user, I want the map to automatically show the entire route, so that I do not need to manually zoom or pan.

#### Acceptance Criteria

1. WHEN a route is displayed and Route_Geometry contains at least two coordinates, THE GUI_Application SHALL compute the Bounding_Box as the minimum latitude, maximum latitude, minimum longitude, and maximum longitude spanning all coordinates in Route_Geometry
2. WHEN the Bounding_Box is computed, THE Map_Widget SHALL adjust the Zoom_Level to the largest integer zoom value (between 1 and 19) such that the Bounding_Box fits within the visible Viewport
3. WHEN the Zoom_Level is determined, THE Map_Widget SHALL center the Viewport on the geographic midpoint of the Bounding_Box
4. WHEN adjusting the Viewport, THE Map_Widget SHALL add 24 pixels of padding on each edge (top, bottom, left, right) between the Bounding_Box and the Viewport border
5. WHEN a user requests a new route while a previous route is displayed, THE Map_Widget SHALL compute and apply the new Bounding_Box for the new route within 200 milliseconds of receiving the route data
6. WHEN Route_Geometry contains fewer than two coordinates, THE Map_Widget SHALL center the Viewport on the single coordinate (if present) at zoom level 15
7. WHEN Route_Geometry contains invalid coordinates (latitude outside ±90° or longitude outside ±180°), THE Map_Widget SHALL exclude those coordinates from the Bounding_Box calculation

### Requirement 5: Support Map Pan Interaction

**User Story:** As a desktop user, I want to drag the map to view areas outside the initial viewport, so that I can explore the route context.

#### Acceptance Criteria

1. WHEN the user presses the left mouse button while the cursor is positioned over the Map_Widget, THE Map_Widget SHALL record the cursor's pixel coordinates as the pan origin
2. WHILE the left mouse button remains pressed, THE Map_Widget SHALL translate the map content by the vector difference between the current cursor position and the pan origin, updating at least 30 times per second
3. WHEN the left mouse button is released or the cursor exits the Map_Widget bounds, THE Map_Widget SHALL stop translating the map content and finalize the current Viewport position
4. WHEN the Viewport position changes during a pan operation, THE Map_Widget SHALL identify newly visible tile coordinates and request any tiles not already cached
5. WHEN tile loading fails during a pan operation, THE Map_Widget SHALL continue to respond to pan gestures without interruption

### Requirement 6: Support Map Zoom Interaction

**User Story:** As a desktop user, I want to zoom in and out on the map, so that I can see more or less detail.

#### Acceptance Criteria

1. WHEN the user scrolls the mouse wheel forward (away from the user) over the Map_Widget, THE Map_Widget SHALL increment the Zoom_Level by 1 integer step
2. WHEN the user scrolls the mouse wheel backward (toward the user) over the Map_Widget, THE Map_Widget SHALL decrement the Zoom_Level by 1 integer step
3. THE Map_Widget SHALL clamp Zoom_Level to the inclusive range [1, 19], such that incrementing at level 19 leaves Zoom_Level unchanged, and decrementing at level 1 leaves Zoom_Level unchanged
4. WHEN Zoom_Level changes, THE Map_Widget SHALL request new tiles with zoom coordinate matching the new Zoom_Level value and re-render Route_Geometry at the new scale
5. WHEN the Route_Geometry polyline is displayed and the user changes Zoom_Level, THE Map_Widget SHALL preserve the polyline's color (#0066CC), stroke width (5 pixels), and opacity (0.85) at the new zoom
6. WHEN tile loading fails after a zoom operation, THE Map_Widget SHALL display placeholder rectangles for missing tiles and continue to respond to subsequent zoom operations

### Requirement 7: Fetch and Cache Map Tiles

**User Story:** As a desktop user, I want the map to load quickly without re-downloading tiles I have already seen, so that interaction remains smooth.

#### Acceptance Criteria

1. WHEN the Map_Widget calculates visible tiles for the current Viewport and Zoom_Level, THE Map_Widget SHALL construct tile URLs for the Tile_Provider using the zoom/x/y coordinate system
2. WHEN the Map_Widget requests a tile not present in cache, THE Map_Widget SHALL download the tile image over HTTPS from the Tile_Provider with a timeout of 10 seconds
3. IF a tile download fails due to network error or timeout, THEN THE Map_Widget SHALL retry up to 2 additional times with 1 second delay between attempts
4. IF a tile download fails after all retry attempts, THEN THE Map_Widget SHALL display a placeholder image indicating the tile is unavailable
5. WHEN the Map_Widget receives tile data from the Tile_Provider, THE Map_Widget SHALL validate that the data is a valid PNG or JPEG image format
6. IF received tile data is not a valid image format, THEN THE Map_Widget SHALL discard the data and display a placeholder image for that tile
7. WHEN the Map_Widget successfully downloads and validates a tile image, THE Map_Widget SHALL store it in memory cache keyed by zoom/x/y coordinates
8. THE Map_Widget SHALL limit the memory cache to a maximum of 500 tiles
9. WHEN the memory cache reaches 500 tiles and a new tile must be cached, THE Map_Widget SHALL evict the least recently accessed tile
10. WHEN the Map_Widget needs to render a tile that is already cached, THE Map_Widget SHALL retrieve and render the cached image without initiating a download

### Requirement 8: Handle Tile Download Failures Gracefully

**User Story:** As a desktop user, I want the map to remain usable even when some tiles fail to load, so that network issues do not break the application.

#### Acceptance Criteria

1. WHEN a tile download exceeds the 10-second timeout specified in Requirement 7, THE Map_Widget SHALL render a placeholder rectangle with RGB color (230, 230, 230) and a 1-pixel solid border with RGB color (200, 200, 200) for that tile
2. WHEN a tile download receives an HTTP response with status code 400-599, THE Map_Widget SHALL render the placeholder rectangle described in criterion 1 for that tile
3. WHEN a tile download fails due to DNS resolution failure or connection refused error, THE Map_Widget SHALL render the placeholder rectangle described in criterion 1 for that tile
4. WHEN any tile displays as a placeholder, THE Map_Widget SHALL allow the user to pan the map by dragging the mouse while holding the left button
5. WHEN any tile displays as a placeholder, THE Map_Widget SHALL allow the user to zoom the map by scrolling the mouse wheel
6. THE Map_Widget SHALL NOT retry downloading a tile that has been rendered as a placeholder unless the user changes the Zoom_Level or pans the Viewport such that the tile is no longer visible and then returns to it

### Requirement 9: Preserve Text Directions Alongside Map

**User Story:** As a desktop user, I want to see both the map and the text directions, so that I can use whichever is more helpful.

#### Acceptance Criteria

1. WHEN a successful route request completes, THE GUI_Application SHALL display both the Map_Widget and the text directions widget in a vertical layout with the Map_Widget at grid row 1 and the text directions widget at grid row 2
2. THE text directions widget SHALL remain scrollable via its attached vertical scrollbar after the Map_Widget is added
3. THE text directions widget SHALL display the same numbered turn-by-turn instructions with distance values as the current implementation without modification
4. WHEN the window height is less than 720 pixels (insufficient to show both the Map_Widget at 300 pixels and the text directions widget at 16 lines of text), THE GUI_Application SHALL allocate the available height equally between the Map_Widget and the text directions widget, with each receiving independent scrollbars if their content exceeds their allocated height

### Requirement 10: Clear Map When Route Request Fails

**User Story:** As a desktop user, I want the map to clear when a route fails, so that I do not see stale data from a previous request.

#### Acceptance Criteria

1. WHEN the GUI_Application detects a client-side validation failure (empty origin or destination input), THE Map_Widget SHALL remove any displayed polyline and all Markers from the map
2. WHEN a route request fails with an HTTP error response (status codes 400-599), THE Map_Widget SHALL remove any displayed polyline and all Markers from the map
3. WHEN a route request exceeds a 30-second timeout without receiving a response, THE Map_Widget SHALL remove any displayed polyline and all Markers from the map
4. WHEN a route request receives an invalid response (missing "paths" key or unparseable JSON), THE Map_Widget SHALL remove any displayed polyline and all Markers from the map
5. WHEN route elements are cleared due to failure, THE Map_Widget SHALL continue displaying base map tiles at the current Viewport and Zoom_Level
6. WHEN the user clicks the "Clear" button, THE Map_Widget SHALL remove all route elements (polyline and Markers) and reset the Viewport to latitude 0°, longitude 0° with zoom level 2
7. WHEN a route request fails, THE status bar SHALL display an error message describing the failure type

### Requirement 11: Attribute Map Tile Provider

**User Story:** As a developer, I want to comply with the Tile_Provider's terms of service, so that the application remains legally usable.

#### Acceptance Criteria

1. THE Map_Widget SHALL display a text label containing "© OpenStreetMap contributors" with font size 10 pixels and white color with 80% opacity
2. THE attribution label SHALL be positioned 5 pixels from the bottom edge and 5 pixels from the right edge of the Map_Widget
3. THE attribution label SHALL be drawn with a z-index higher than map tiles and route elements so it is never obscured
4. THE attribution label SHALL use a semi-transparent black background (RGB 0, 0, 0 with 50% opacity) to achieve a contrast ratio of at least 4.5:1 against tile colors
5. WHEN the user pans the map, THE attribution label SHALL remain fixed at the bottom-right corner of the Map_Widget without moving relative to the widget borders
6. WHEN the user zooms the map, THE attribution label SHALL remain fixed at the bottom-right corner of the Map_Widget without changing size or position relative to the widget borders

### Requirement 12: Reuse Existing Route Data Structure

**User Story:** As a developer, I want the map feature to use the existing API result format, so that no backend changes are required.

#### Acceptance Criteria

1. THE GUI_Application SHALL extract Route_Geometry by reading the value at dictionary path `result["data"]["paths"][0]["points"]["coordinates"]`
2. IF the extraction fails because any key in the path does not exist, THEN THE GUI_Application SHALL log the missing key and proceed to render the Map_Widget without route geometry
3. IF the "paths" list is empty, THEN THE GUI_Application SHALL log the absence and proceed to render the Map_Widget without route geometry
4. WHEN Route_Geometry is successfully extracted, THE GUI_Application SHALL verify that each element is a list or tuple containing at least two numeric elements
5. THE GUI_Application SHALL interpret the first numeric element of each coordinate as longitude and the second numeric element as latitude (matching GraphHopper's [longitude, latitude] format)
6. THE GUI_Application SHALL convert each [longitude, latitude] pair to [latitude, longitude] format before passing coordinates to the Map_Widget

### Requirement 13: Integrate Map Library with Minimal Dependencies

**User Story:** As a developer, I want the map feature to use a lightweight library, so that installation remains simple and cross-platform.

#### Acceptance Criteria

1. THE GUI_Application SHALL import the `tkintermapview` package and instantiate a TkinterMapView widget as the Map_Widget
2. THE requirements.txt file SHALL contain the entry `tkintermapview==1.29` (exact version pin using == operator)
3. WHEN the GUI_Application imports tkintermapview and calls `TkinterMapView(parent)`, THE import SHALL succeed and return a widget instance ready to be added to the tkinter grid layout
4. IF the tkintermapview import fails with ImportError, THEN THE GUI_Application SHALL display an error message in the status bar instructing the user to run `pip install -r requirements.txt` and disable map functionality
5. THE Map_Widget SHALL render map tiles and respond to pan and zoom interactions on Windows, macOS, and Linux operating systems using only the Python standard library tkinter module and the tkintermapview package

### Requirement 14: Maintain Thread Safety for Background Requests

**User Story:** As a developer, I want map updates to occur on the GUI thread only, so that the existing threading model remains safe.

#### Acceptance Criteria

1. THE background worker thread SHALL extract Route_Geometry from the API result dictionary by reading `result["data"]["paths"][0]["points"]["coordinates"]`
2. IF the extraction fails due to missing keys or invalid data structure, THEN THE background worker thread SHALL include an empty list for Route_Geometry in the result dictionary passed to the GUI thread
3. THE background worker thread SHALL pass the extracted Route_Geometry to the GUI thread by calling `root.after(0, callback, result)` where `result` includes the Route_Geometry data
4. THE GUI thread SHALL receive the result via the callback function and update the Map_Widget (add polyline, place Markers, adjust Viewport) within that callback
5. THE Map_Widget instance SHALL be accessed only from the GUI thread and never directly from the background worker thread
6. WHEN the user closes the window before a route request completes, THE GUI_Application SHALL set the `_closing` flag to True and THE callback SHALL check this flag and skip all Map_Widget updates if True

### Requirement 15: Provide Visual Feedback During Route Requests

**User Story:** As a desktop user, I want to see that the map is updating when I request a route, so that I know the application is working.

#### Acceptance Criteria

1. WHEN the user clicks the "Find route" button, THE GUI_Application SHALL remove any previously displayed polyline, Markers, and popup labels from the Map_Widget
2. THE status bar SHALL display the text "Searching..." within 50 milliseconds of the user clicking the "Find route" button
3. WHEN the route result arrives from the background thread, THE Map_Widget SHALL render the new polyline and Markers within 100 milliseconds of the callback execution
4. WHEN the Map_Widget completes rendering and the text directions widget has been updated, THE status bar SHALL update to display "Done." within 100 milliseconds
5. WHEN a route request fails, THE status bar SHALL display an error message specific to the failure type (e.g., "Route request failed.", "No network connection.") within 100 milliseconds of the failure callback
6. WHEN a route request does not complete within 30 seconds, THE GUI_Application SHALL update the status bar to display "The request timed out" and re-enable the "Find route" button

