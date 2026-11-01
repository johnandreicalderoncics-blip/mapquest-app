# Directions Finder Architecture

## 1. Purpose

Directions Finder is a Python application that resolves place names and
retrieves driving, cycling, or walking routes from the GraphHopper REST API.
It provides three frontends over one shared core:

- a Rich-based command-line interface (`main.py`);
- a tkinter desktop GUI (`gui.py`);
- a local Flask web application (`app.py` + `templates/` + `static/`).

The central architectural rule is separation of concerns:

- network access belongs in `backend/api.py`;
- configuration belongs in `backend/config.py`;
- presentation-neutral formatting belongs in `backend/formatting.py`;
- web validation and route shaping belong in `backend/services.py`;
- terminal presentation belongs in `display.py`;
- CLI orchestration belongs in `main.py`;
- desktop presentation belongs in `gui.py`;
- web presentation belongs in `app.py`, `templates/`, and `static/`.

## 2. Current components

| Component | Responsibility |
|---|---|
| `app.py` | Flask entry point: `GET /`, `POST /route`, friendly 404/500 pages, launches `py app.py` |
| `main.py` | Starts the CLI, collects units/travel mode/locations, and orchestrates requests |
| `gui.py` | Desktop GUI: form widgets, background-thread requests, result rendering |
| `backend/config.py` | Loads the GraphHopper API key from the environment or local configuration |
| `backend/api.py` | Performs geocoding and routing HTTP requests and normalizes expected failures |
| `backend/formatting.py` | Presentation-neutral time/distance/fuel formatting shared by all frontends |
| `backend/services.py` | Web service layer: input validation, key resolution, route-to-template shaping |
| `display.py` | Formats successful routes, errors, distances, durations, and fuel estimates for Rich |
| `templates/index.html` | The single server-rendered page (form, setup banner, errors, results) |
| `static/style.css`, `static/app.js` | Styling and the tiny progressive-enhancement script |
| `config.sample.ini` | Documents the local configuration-file shape without containing a real key |
| `requirements.txt` | Declares third-party Python dependencies |
| `tests/` | unittest suites for the CLI/GUI logic plus pytest tests for services and Flask routes |
| `docs/` | Contains project-selection, team-role, and workload documentation |

## 3. Current execution flow

```text
py main.py
    |
    v
main.main()
    |
    +--> display.show_banner()
    |
    +--> backend.config.get_api_key()
    |
    +--> choose units and travel profile
    |
    +--> ask for origin and destination
    |
    +--> backend.api.fetch_route(...)
              |
              +--> backend.api.geocode(origin)
              |       |
              |       +--> GraphHopper geocoding endpoint
              |
              +--> backend.api.geocode(destination)
              |       |
              |       +--> GraphHopper geocoding endpoint
              |
              +--> GraphHopper routing endpoint
    |
    +--> display.show_result(...)
```

The CLI repeats the location-and-route portion until the user enters `q`,
`quit`, or interrupts the process.

## 4. API result contract

`backend/api.py` shields callers from expected network, HTTP, JSON, and
lookup failures. Callers should not need to catch raw `requests` exceptions
for normal failures.

### Successful route

```python
{
    "ok": True,
    "url": str,
    "data": {
        "paths": [
            {
                "distance": float,       # meters
                "time": float,           # milliseconds
                "instructions": list,
            }
        ]
    },
    "from_name": str,
    "to_name": str,
}
```

### Failed route

```python
{
    "ok": False,
    "title": str,
    "detail": str,
}
```

New frontends should preserve this contract. A frontend should display
`title` and `detail` rather than exposing a traceback or raw HTTP response.

Note: `"url"` on a success result embeds the API key in its query string.
The CLI uses it for its "view on graphhopper" hint; the web frontend must
never forward or render it (`backend/services.py` strips it, and
`tests/test_services.py` / `tests/test_app.py` enforce that with a
key-leak guard).

## 5. Units and route data

GraphHopper returns distances in meters and times in milliseconds.
`backend/formatting.py` converts these values for every frontend:

- metric distance: kilometers;
- imperial distance: miles;
- duration: `hh:mm:ss`;
- driving fuel: an explicitly labeled estimate;
- bicycle and walking fuel: not applicable.

No frontend displays raw meters or milliseconds as if they were user-facing
units, and none imports another frontend's presentation code.

## 6. Browser frontend boundary

The web frontend is a local Flask application in `app.py` with its service
layer in `backend/services.py`. The browser is the presentation layer;
Python remains the local web server and API client:

```text
py app.py
    |
    v
Browser loads http://127.0.0.1:5000
    |
    +--> GET /: form page (setup banner when no key is configured)
    |
    +--> form POSTs origin, destination, units, and profile to /route
    |
    +--> app.py normalizes form values, backend.services validates them
    |
    +--> backend.api.fetch_route(...)
    |
    +--> backend.services.get_route(...) shapes a template-ready dict
    |
    +--> templates/index.html renders the summary and directions
```

The web frontend must not call `main.main()` because `main.py` owns console
prompts. It must also not call `display.show_result()` because that function
writes Rich terminal output. All three frontends share the API,
configuration, and formatting layers while retaining independent
presentation layers.

## 7. Local server and executable model

The normal development flow is:

```text
py app.py
    |
    +--> start localhost web server (127.0.0.1:5000)
    +--> open default browser
    +--> browser sends HTTP requests
    +--> server calls backend/api.py
```

If a no-Python installation is required, package the server with PyInstaller.
The executable should still start a localhost server and open the browser.
The executable is a deployment wrapper, not a replacement for the browser
frontend. Templates and static files must be bundled and resolved through a
reliable resource path.

The server binds to `127.0.0.1` by default so the application is not
unintentionally exposed to other devices on the network.

## 8. Configuration and secret handling

The API key is resolved in this order:

1. `GRAPHOPPER_KEY` environment variable;
2. local `config.ini` at the project root (one level above `backend/`);
3. no usable key, which requires setup guidance.

The real key must not be hard-coded in Python, included in web pages,
written to logs, or committed to Git. `config.ini` is intentionally
git-ignored, while `config.sample.ini` contains only a placeholder.

`backend.config.load_api_key()` returns `None` instead of printing and
exiting; the web and GUI frontends use it and show the setup message
themselves. `backend.config.get_api_key()` remains the CLI's entry point
and reproduces the original setup message exactly.

## 9. Extension rules

When adding behavior:

- add API parameters and endpoint logic to `backend/api.py`;
- add configuration sources to `backend/config.py`;
- add shared formatting to `backend/formatting.py`;
- add CLI prompts to `main.py`;
- add Rich terminal rendering to `display.py`;
- add GUI widgets and GUI rendering to `gui.py`;
- add web validation and route shaping to `backend/services.py`;
- add HTTP routes to `app.py`;
- add browser markup to `templates/`;
- add styling and small browser behavior to `static/`.

Avoid importing one presentation layer into another. This keeps the CLI
available for terminal use and allows each frontend to evolve
independently.

## 10. Verification checklist

Any frontend change should verify:

- `py main.py` remains available;
- `py gui.py` remains available;
- `py app.py` starts successfully and serves the browser frontend;
- empty locations are rejected before network access;
- successful routes display converted units and instructions;
- API failures display a clear error;
- the server is localhost-only by default;
- no API key is present in source, tests, logs, or documentation;
- `py -m pytest tests -q` passes (CLI/GUI suites run under pytest too).
