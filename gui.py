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

import threading
import tkinter as tk
from tkinter import ttk

from backend import api, config, formatting


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
                        profile: str) -> threading.Thread:
    """Run run_route_request on a daemon thread.

    The worker touches no widgets: it schedules exactly one callback
    via root.after(0, on_result, result), tkinter's supported
    thread-to-GUI-thread bridge. Returns the thread so tests can join
    it.
    """
    def worker() -> None:
        result = run_route_request(key, origin, destination,
                                   units, profile)
        root.after(0, on_result, result)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
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
        lines.append(f"{number}. {text} "
                     f"({formatting.format_distance(step.get('distance', 0),
                                                    units)})")
    return lines


class RouteApp:
    """Widget wiring only; the logic lives in the functions above."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._closing = False
        root.title("Directions Finder")
        root.minsize(560, 420)

        self.origin_var = tk.StringVar()
        self.destination_var = tk.StringVar()
        self.units_var = tk.StringVar(value="imperial")  # CLI default
        self.profile_var = tk.StringVar(value="car")     # CLI default

        self._build_input_frame()
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
        self.search_button = ttk.Button(button_box, text="Find route",
                                        command=self._on_search)
        self.search_button.pack(side="left")
        ttk.Button(button_box, text="Clear",
                   command=self._on_clear).pack(side="left", padx=(8, 0))

    def _build_result_area(self) -> None:
        frame = ttk.Frame(self.root, padding=(12, 6))
        frame.grid(row=1, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.result_text = tk.Text(frame, height=16, wrap="word",
                                   state="disabled")
        self.result_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical",
                                  command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.tag_configure("heading", font=("TkDefaultFont",
                                                        10, "bold"))
        self.result_text.tag_configure("error", foreground="#b00020")

        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

    def _build_status_bar(self) -> None:
        self.status_var = tk.StringVar(
            value="Enter a starting location and a destination.")
        ttk.Label(self.root, textvariable=self.status_var, anchor="w",
                  padding=(12, 4)).grid(row=2, column=0, sticky="ew")

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
        start_route_request(self.root, self._on_result, key,
                            self.origin_var.get().strip(),
                            self.destination_var.get().strip(),
                            self.units_var.get(), self.profile_var.get())

    def _on_result(self, result: dict) -> None:
        if self._closing:
            return  # window already destroyed - drop the stale result
        self.search_button.configure(state="normal")
        try:
            failure = not result.get("ok")
            self._render_lines(result_to_lines(
                result, self.units_var.get(), self.profile_var.get()),
                error=failure)
            self.status_var.set("Done." if not failure
                                else "Route request failed.")
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
