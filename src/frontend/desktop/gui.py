"""Desktop GUI for the Directions app (tkinter).

Run with:  py gui.py

This is the GUI presentation layer described in ARCHITECTURE.md section
6. It shares backend/api.py and backend/config.py with the CLI and web
frontend but never imports main.py (which owns console prompts) or
display.py (which owns Rich terminal rendering). All route formatting
comes from backend/formatting.py so every frontend shows identical
numbers.

Threading model (ARCHITECTURE.md section 7): the route request runs on
a daemon worker thread; the worker only ever calls root.after(...) to
hand its result back, and every widget update happens on the GUI
thread. A _closing flag drops results that arrive after the window is
destroyed.

RouteApp is the project's first class - a deliberate exception to the
usual functional style, because tkinter callbacks need shared widget
state. All actual logic lives in the module-level pure functions below,
which are the parts the unit tests exercise (no Tk needed).
"""

import logging
import threading
import time
import tkinter as tk
from tkinter import ttk

from backend import api, config, formatting

COLOR_PRIMARY = "#1a73e8"
COLOR_PRIMARY_DARK = "#1557b0"
COLOR_PRIMARY_PALE = "#e8f0fe"
COLOR_PAGE = "#f8f9fa"
COLOR_CARD = "#ffffff"
COLOR_HOVER = "#f1f3f4"
COLOR_ACTIVE = "#e8eaed"
COLOR_TEXT = "#202124"
COLOR_MUTED = "#5f6368"
COLOR_BORDER = "#dadce0"
COLOR_BORDER_LIGHT = "#e8eaed"
COLOR_ERROR = "#d93025"
FONT_BODY = ("Nunito", 10)
FONT_DISPLAY = ("Baloo 2", 16, "bold")
FONT_LABEL = ("Nunito", 10, "bold")

try:
    from src.frontend.desktop.map_widget import MapWidget, extract_route_geometry
    MAP_WIDGET_AVAILABLE = True
except ImportError:
    MAP_WIDGET_AVAILABLE = False
    MapWidget = None
    extract_route_geometry = None



class StyledButton(tk.Button):
    """Custom button with hover effects matching design.md color palette.
    
    This class provides properly styled buttons for Windows where ttk.Style
    has limited support for background colors. Primary buttons use the web
    frontend blue while secondary buttons use the card surface treatment.
    
    Args:
        parent: Parent widget
        is_primary: If True, applies primary blue styling. If False, applies secondary gray styling.
        **kwargs: Additional tk.Button keyword arguments
    """
    def __init__(self, parent, **kwargs):
        # Extract custom style params
        is_primary = kwargs.pop('is_primary', False)
        
        if is_primary:
            # Primary button (Find Route) - Design.md Primary Blue
            bg_color = COLOR_PRIMARY
            fg_color = 'white'
            active_bg = COLOR_PRIMARY_DARK
            hover_bg = '#4285f4'
            disabled_bg = COLOR_BORDER
            disabled_fg = COLOR_MUTED
        else:
            # Secondary button (Clear) - Design.md Light Gray
            bg_color = COLOR_CARD
            fg_color = COLOR_TEXT
            active_bg = COLOR_ACTIVE
            hover_bg = COLOR_HOVER
            disabled_bg = COLOR_CARD
            disabled_fg = COLOR_MUTED
        
        super().__init__(parent,
                        bg=bg_color,
                        fg=fg_color,
                        activebackground=active_bg,
                        activeforeground='white' if is_primary else fg_color,
                        disabledforeground=disabled_fg,
                        relief='flat',
                        borderwidth=0 if is_primary else 1,
                        highlightbackground=COLOR_BORDER,
                        highlightthickness=0,
                        padx=12,
                        pady=8,
                        cursor='hand2',
                        font=FONT_BODY,
                        **kwargs)
        
        # Store colors for hover effects
        self.default_bg = bg_color
        self.hover_bg = hover_bg
        self.disabled_bg = disabled_bg
        self.is_primary = is_primary
        
        # Add hover effects
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        """Handle mouse enter - show hover color if button is enabled."""
        if str(self['state']) != 'disabled':
            self.config(bg=self.hover_bg)
    
    def _on_leave(self, event):
        """Handle mouse leave - restore default color."""
        if str(self['state']) != 'disabled':
            self.config(bg=self.default_bg)
    
    def configure(self, **kwargs):
        """Override configure to handle disabled state background color."""
        if 'state' in kwargs:
            if kwargs['state'] == 'disabled':
                super().configure(bg=self.disabled_bg, **kwargs)
            else:
                super().configure(bg=self.default_bg, **kwargs)
        else:
            super().configure(**kwargs)
    
    config = configure  # Alias for tkinter compatibility


logger = logging.getLogger(__name__)


def validate_inputs(origin: str, destination: str) -> str | None:
    """Reject empty or whitespace-only locations before any request.

    Returns an error message, or None when both inputs are usable.
    """
    if not origin.strip():
        return "Please enter a starting location."
    if not destination.strip():
        return "Please enter a destination."
    return None


def run_route_request(key: str, origin: str, destination: str,
                      units: str, profile: str) -> dict:
    """Fetch a route, converting unexpected crashes to failure dicts.

    api.fetch_route already returns friendly failure dictionaries for
    expected problems; this wrapper also catches anything unexpected so
    a programming error can never look like a successful route.
    """
    try:
        return api.fetch_route(key, origin, destination, units, profile)
    except Exception as exc:  # surfaced in the GUI, never swallowed
        return {"ok": False, "title": "Unexpected error",
                "detail": f"{type(exc).__name__}: {exc}"}


def start_route_request(root: tk.Misc, on_result, key: str, origin: str,
                        destination: str, units: str,
                        profile: str, timeout_seconds: int = 30) -> threading.Thread:
    """Run run_route_request on a daemon thread with timeout.

    The worker touches no widgets: it schedules exactly one callback
    via root.after(0, on_result, result), tkinter's supported
    thread-to-GUI-thread bridge. Returns the thread so tests can join
    it.
    
    If the request does not complete within timeout_seconds, a timeout
    result is delivered instead.
    """
    result_delivered = threading.Event()
    
    def worker() -> None:
        try:
            result = run_route_request(key, origin, destination,
                                       units, profile)
            if not result_delivered.is_set():
                result_delivered.set()
                root.after(0, on_result, result)
        except Exception as exc:
            # Unexpected error in worker thread - deliver failure result
            if not result_delivered.is_set():
                result_delivered.set()
                root.after(0, on_result, {
                    "ok": False,
                    "title": "Unexpected error in background thread",
                    "detail": f"{type(exc).__name__}: {exc}"
                })
    
    def timeout_handler() -> None:
        """Check for timeout and deliver timeout result if needed."""
        try:
            if not result_delivered.wait(timeout=timeout_seconds):
                # Timeout occurred - deliver timeout result
                result_delivered.set()
                root.after(0, on_result, {
                    "ok": False,
                    "title": "The request timed out",
                    "detail": f"The route request did not complete within {timeout_seconds} seconds. "
                              "Please try again."
                })
        except Exception as exc:
            # Unexpected error in timeout handler
            if not result_delivered.is_set():
                result_delivered.set()
                root.after(0, on_result, {
                    "ok": False,
                    "title": "Timeout handling error",
                    "detail": f"{type(exc).__name__}: {exc}"
                })

    thread = threading.Thread(target=worker, daemon=True)
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    thread.start()
    timeout_thread.start()
    return thread


def result_to_lines(result: dict, units: str, profile: str) -> list[str]:
    """Turn an api.fetch_route result dict into plain display lines.

    Pure function (no tkinter, no Rich) so tests can assert exactly
    what the GUI would render. Success mirrors display.show_route's
    summary and turn-by-turn content; failure shows title and detail.
    """
    if not result.get("ok"):
        return ["Route request failed:",
                result.get("title", "Unknown error"),
                "",
                result.get("detail", "")]

    labels = formatting.UNIT_LABELS[units]
    path = result["data"]["paths"][0]
    meters = path.get("distance", 0)
    lines = [
        f"From: {result.get('from_name', '-')}",
        f"To: {result.get('to_name', '-')}",
        f"Travel mode: {formatting.PROFILE_LABELS.get(profile, profile)}",
        f"Trip duration: {formatting.format_time(path.get('time', 0))}",
        f"Distance ({labels['distance']}): "
        f"{formatting.format_distance(meters, units)}",
        f"Fuel used ({labels['fuel']}): "
        f"{formatting.format_fuel_estimate(meters, units, profile)}",
        "",
        "Turn-by-turn directions:",
    ]
    instructions = path.get("instructions", [])
    if not instructions:
        lines.append("No turn-by-turn instructions were returned for "
                     "this route.")
        return lines
    # Step distances are meters; format_distance() converts them to the
    # user's chosen unit.
    for number, step in enumerate(instructions, start=1):
        text = step.get("text") or "(no description)"
        distance = formatting.format_distance(step.get("distance", 0), units)
        lines.append(f"{number}. {text} ({distance})")
    return lines


def _configure_styles(root: tk.Tk) -> ttk.Style:
    """Configure ttk styles to match the web frontend design tokens."""
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass
    style.configure('Primary.TButton',
                   background=COLOR_PRIMARY,
                   foreground='white',
                   borderwidth=0,
                   focuscolor=COLOR_PRIMARY_PALE,
                   padding=(8, 6),
                   font=FONT_BODY)
    style.map('Primary.TButton',
             background=[('active', COLOR_PRIMARY_DARK),
                        ('pressed', COLOR_PRIMARY_DARK),
                        ('disabled', COLOR_BORDER)],
             foreground=[('disabled', COLOR_MUTED)])
    style.configure('Secondary.TButton',
                   background=COLOR_CARD,
                   foreground=COLOR_TEXT,
                   borderwidth=1,
                   bordercolor=COLOR_BORDER,
                   padding=(8, 6),
                   font=FONT_BODY)
    style.map('Secondary.TButton',
             background=[('active', COLOR_HOVER),
                        ('pressed', COLOR_ACTIVE)])
    style.configure('TEntry',
                   fieldbackground=COLOR_CARD,
                   foreground=COLOR_TEXT,
                   borderwidth=1,
                   relief='solid',
                   padding=(8, 6))
    style.map('TEntry',
             bordercolor=[('focus', COLOR_PRIMARY)],
             lightcolor=[('focus', COLOR_PRIMARY)],
             darkcolor=[('focus', COLOR_PRIMARY)])
    style.configure('TLabel',
                   foreground=COLOR_MUTED,
                   background=COLOR_PAGE,
                   font=FONT_BODY)
    style.configure('TLabelframe',
                   borderwidth=1,
                   relief='solid',
                   bordercolor=COLOR_BORDER_LIGHT,
                   background=COLOR_CARD)
    style.configure('TLabelframe.Label',
                   foreground=COLOR_TEXT,
                   background=COLOR_CARD,
                   font=FONT_LABEL)
    style.configure('TRadiobutton',
                   foreground=COLOR_MUTED,
                   background=COLOR_CARD,
                   font=FONT_BODY)
    style.map('TRadiobutton',
             background=[('active', COLOR_HOVER)])
    style.configure('TFrame',
                   background=COLOR_PAGE)
    return style


class RouteApp:
    """Widget wiring only; the logic lives in the functions above."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._closing = False
        root.title("Directions Finder")
        root.minsize(560, 420)
        root.configure(bg=COLOR_PAGE)
        self.style = _configure_styles(root)

        self.origin_var = tk.StringVar()
        self.destination_var = tk.StringVar()
        self.units_var = tk.StringVar(value="imperial")  # CLI default
        self.profile_var = tk.StringVar(value="car")     # CLI default
        self.status_var = tk.StringVar(
            value="Enter a starting location and a destination.")
        self.map_widget: MapWidget = None

        self._build_input_frame()
        self._build_map_widget()
        self._build_result_area()
        self._build_status_bar()

        root.protocol("WM_DELETE_WINDOW", self._on_close)
        root.bind("<Return>", lambda event: self._on_search())

    # --- widget construction -----------------------------------------
    def _build_input_frame(self) -> None:
        frame = ttk.Frame(self.root, padding=(12, 12, 12, 6))
        frame.grid(row=0, column=0, sticky="ew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="From:").grid(row=0, column=0,
                                            sticky="w", pady=2)
        origin_entry = ttk.Entry(frame, textvariable=self.origin_var)
        origin_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=(8, 0))

        ttk.Label(frame, text="To:").grid(row=1, column=0,
                                          sticky="w", pady=2)
        destination_entry = ttk.Entry(frame,
                                      textvariable=self.destination_var)
        destination_entry.grid(row=1, column=1, sticky="ew", pady=2,
                               padx=(8, 0))

        units_box = ttk.LabelFrame(frame, text="Units", padding=(8, 2))
        units_box.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Radiobutton(units_box, text="Metric (km)",
                        value="metric", variable=self.units_var
                        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(units_box, text="Imperial (mi)",
                        value="imperial", variable=self.units_var
                        ).pack(side="left")

        mode_box = ttk.LabelFrame(frame, text="Travel mode",
                                  padding=(8, 2))
        mode_box.grid(row=3, column=0, columnspan=2, sticky="ew",
                      pady=(8, 0))
        ttk.Radiobutton(mode_box, text="Car", value="car",
                        variable=self.profile_var).pack(side="left",
                                                        padx=(0, 12))
        ttk.Radiobutton(mode_box, text="Bicycle", value="bike",
                        variable=self.profile_var).pack(side="left",
                                                        padx=(0, 12))
        ttk.Radiobutton(mode_box, text="Walking", value="walk",
                        variable=self.profile_var).pack(side="left")

        button_box = ttk.Frame(frame)
        button_box.grid(row=4, column=0, columnspan=2, sticky="ew",
                        pady=(12, 0))
        self.search_button = StyledButton(button_box, text="Find route",
                                        command=self._on_search,
                                        is_primary=True)
        self.search_button.pack(side="left")
        StyledButton(button_box, text="Clear",
                   command=self._on_clear,
                   is_primary=False).pack(side="left", padx=(8, 0))

    def _build_map_widget(self) -> None:
        """Initialize and place MapWidget at grid row 1.
        
        Shows error in status bar if tkintermapview import fails.
        """
        if not MAP_WIDGET_AVAILABLE:
            self.status_var.set(
                "Map widget unavailable: tkintermapview not installed. "
                "Run: pip install tkintermapview"
            )
            return
        
        try:
            frame = ttk.Frame(self.root)
            frame.grid(row=1, column=0, sticky="nsew")
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            
            self.map_widget = MapWidget(frame)
            self.map_widget.get_widget().grid(row=0, column=0, sticky="nsew")
            
            # Configure grid weight for map row
            self.root.rowconfigure(1, weight=1)
            
        except Exception as exc:
            error_msg = f"Map widget initialization failed: {type(exc).__name__}: {exc}"
            self.status_var.set(error_msg)
            self.map_widget = None

    def _build_result_area(self) -> None:
        frame = ttk.Frame(self.root, padding=(12, 6))
        frame.grid(row=2, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.result_text = tk.Text(
            frame,
            height=16,
            wrap="word",
            state="disabled",
            background=COLOR_CARD,
            foreground=COLOR_TEXT,
            insertbackground=COLOR_PRIMARY,
            selectbackground=COLOR_PRIMARY_PALE,
            selectforeground=COLOR_TEXT,
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER_LIGHT,
            highlightcolor=COLOR_PRIMARY,
            padx=12,
            pady=10,
            font=FONT_BODY,
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical",
                                  command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.tag_configure("heading", font=FONT_LABEL,
                                       foreground=COLOR_TEXT)
        self.result_text.tag_configure("error", foreground=COLOR_ERROR)

        self.root.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)

    def _build_status_bar(self) -> None:
        ttk.Label(self.root, textvariable=self.status_var, anchor="w",
                  padding=(12, 4)).grid(row=3, column=0, sticky="ew")

    # --- result rendering (GUI thread only) ----------------------------
    def _render_lines(self, lines: list[str], error: bool) -> None:
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        if error:
            self.result_text.insert("end", "\n".join(lines) + "\n", "error")
        else:
            for line in lines:
                if line.endswith(":") and line and not line[0].isdigit():
                    self.result_text.insert("end", line + "\n", "heading")
                else:
                    self.result_text.insert("end", line + "\n")
        self.result_text.configure(state="disabled")

    # --- event handlers (GUI thread only) -------------------------------
    def _on_search(self) -> None:
        if self._closing:
            return
        error = validate_inputs(self.origin_var.get(),
                                self.destination_var.get())
        if error:
            self.status_var.set(error)
            self._render_lines([error], error=True)
            return

        # Re-checked per click so a key added while the window is open
        # is picked up without restarting the app.
        key = config.load_api_key()
        if key is None:
            self.status_var.set("No GraphHopper API key configured.")
            self._render_lines(config.SETUP_MESSAGE.splitlines(), error=True)
            return

        self.status_var.set("Searching...")
        self.search_button.configure(state="disabled")
        
        if self.map_widget is not None:
            try:
                self.map_widget.clear_route()
            except Exception as exc:
                # Log error but continue with route request
                logger.error(f"Error clearing map: {exc}", exc_info=True)

        start_route_request(self.root, self._on_result, key,
                            self.origin_var.get().strip(),
                            self.destination_var.get().strip(),
                            self.units_var.get(), self.profile_var.get())

    def _on_result(self, result: dict) -> None:
        if self._closing:
            return  # window already destroyed - drop the stale result
        
        callback_start = time.perf_counter()
        
        try:
            # Re-enable button (was disabled in _on_search)
            self.search_button.configure(state="normal")
            
            # Track if map rendering failed (to update status appropriately)
            map_render_error = None
            
            failure = not result.get("ok")
            
            # Update map based on success or failure
            if MAP_WIDGET_AVAILABLE and self.map_widget is not None:
                try:
                    if not failure:
                        # Success: Render route on map
                        render_start = time.perf_counter()
                        
                        # Extract coordinates from result
                        coordinates = extract_route_geometry(result)
                        
                        # Render route if coordinates are non-empty
                        if coordinates:
                            self.map_widget.render_route(coordinates)
                            
                            render_elapsed = (time.perf_counter() - render_start) * 1000
                            if render_elapsed > 100:
                                logger.warning(
                                    f"Map rendering took {render_elapsed:.1f}ms "
                                    f"(exceeds 100ms threshold)"
                                )
                            else:
                                logger.debug(f"Map rendered in {render_elapsed:.1f}ms")
                        else:
                            logger.info("No coordinates to render on map")
                    else:
                        # Failure: Clear map (timeout, network error, etc.)
                        self.map_widget.clear_route()
                        logger.debug("Map cleared due to route request failure")
                        
                except Exception as exc:
                    # Map operation failed, but continue with text directions
                    map_render_error = f"Map update failed: {type(exc).__name__}"
                    logger.error(
                        f"Failed to update map: {exc}",
                        exc_info=True
                    )
            
            # Always update text directions (even if map fails)
            self._render_lines(result_to_lines(
                result, self.units_var.get(), self.profile_var.get()),
                error=failure)
            
            # Update status bar based on result
            if failure:
                # Use the title from the result for specific error messages
                # (e.g., "The request timed out", "No network connection")
                error_title = result.get("title", "Route request failed")
                self.status_var.set(error_title)
            elif map_render_error:
                self.status_var.set(map_render_error)
            else:
                self.status_var.set("Done.")
            
            callback_elapsed = (time.perf_counter() - callback_start) * 1000
            if callback_elapsed > 100:
                logger.warning(
                    f"Result callback took {callback_elapsed:.1f}ms "
                    f"(exceeds 100ms threshold)"
                )
            else:
                logger.debug(f"Result callback completed in {callback_elapsed:.1f}ms")
                
        except Exception as exc:  # never crash the event loop
            self.status_var.set("Unexpected error while rendering.")
            self._render_lines(
                ["Unexpected error while rendering the route:",
                 f"{type(exc).__name__}: {exc}"], error=True)

    def _on_clear(self) -> None:
        self.origin_var.set("")
        self.destination_var.set("")
        self.units_var.set("imperial")
        self.profile_var.set("car")
        self._render_lines([], error=False)
        self.status_var.set(
            "Enter a starting location and a destination.")
        
        # Reset map widget if available
        if self.map_widget is not None:
            try:
                self.map_widget.reset_view()
            except Exception as exc:
                # Log error but continue - UI clearing is more important
                import logging
                logging.getLogger(__name__).error(
                    f"Failed to reset map view: {type(exc).__name__}: {exc}",
                    exc_info=True
                )

    def _on_close(self) -> None:
        # The worker is a daemon thread, so it cannot keep the process
        # alive; results arriving after this point hit the _closing
        # guard in _on_result.
        self._closing = True
        self.root.destroy()


def main() -> None:
    """Create the window and run the tkinter event loop."""
    root = tk.Tk()
    RouteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
