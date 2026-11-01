# Directions Finder - CLI + GUI + Web (GraphHopper)

A Python application that gets driving, cycling or walking directions
from the [GraphHopper Route API](https://docs.graphhopper.com/) and
shows them as colored, easy-to-read tables in the terminal, in a simple
desktop window, or in your browser.

Built by our team as a **feature enhancement** of the REST API concepts
from Cisco DevNet lab 4.9.2, *Integrate a REST API in a Python
Application* (Project Activity 3). The lab used MapQuest; we use
**GraphHopper** because MapQuest now requires billing information even
for its free tier, while GraphHopper offers a free key with no credit
card - and the lab's concepts (REST request, JSON parsing, status
handling) apply identically.

## Team

| Member | Role |
|---|---|
| John Andrei Calderon | Developer - baseline code, unit selection, GitHub repo |
| Sofia Beatriz Estioco | Developer - table/color output (display layer) |
| Ken Gultiano | Developer - error handling, quality assurance |
| Lawrence Ng | Scrum Leader - project tracking, documentation |

## Features (enhancements over the lab)

1. **Colored, table-formatted output** - trip summary and turn-by-turn
   directions rendered with the [rich](https://github.com/Textualize/rich)
   library; errors appear as red panels, never raw tracebacks.
2. **Metric or imperial units** - pick kilometers/liters or miles/gallons
   at startup (GraphHopper returns meters; conversion happens in
   `display.py`).
3. **Travel mode selection** - car, bicycle or walking (GraphHopper
   profiles).
4. **Built-in geocoding** - type a place name like `Manila, PH`, not
   coordinates; the app resolves it via the GraphHopper Geocoding API.
5. **Fuel estimate for driving routes** - GraphHopper reports no fuel,
   so driving routes show an estimate (8 L/100 km, ~29 mpg), clearly
   labeled as estimated; walking/cycling show N/A.
6. **Robust error handling** - no network, timeouts, invalid/missing API
   key, unknown places and Ctrl+C all produce friendly messages and keep
   the app running where possible.
7. **Desktop GUI** - the same routes in a tkinter window (see
   [GUI](#gui) below); the CLI remains fully available.
8. **Browser app** - the same routes in a local web page, served by
   Flask (see [Browser app](#browser-app) below).

## Requirements

- Python 3.10 or newer
- The `requests`, `rich`, and `flask` packages (plus `pytest` to run
  the tests):

```
py -m pip install -r requirements.txt
```

> On Windows use the `py` launcher as shown. If `python` opens the
> Microsoft Store instead, that is the Windows Store alias - `py` avoids it.

## API key setup (required, free, no credit card)

1. Sign up at <https://graphhopper.com/api/> (free tier - no billing info).
2. In the dashboard, copy your API key.
3. Set it up in **either** of these ways:

**Option A - environment variable**

```
setx GRAPHOPPER_KEY "your-key-here"
```

Open a **new** terminal afterwards so the variable takes effect.

**Option B - config file**

1. Copy `config.sample.ini` in this folder and name the copy `config.ini`.
2. Replace `YOUR_KEY_HERE` with your key.

`config.ini` is listed in `.gitignore`, so your key will **not** be
committed to GitHub. Never paste a real key into any other file.

## Usage

```
py main.py
```

Sample session:

```
Units - (m)etric or (i)mperial (Enter = imperial): m
Travel mode - (c)ar, (b)ike, (w)alk (Enter = car): c
Type 'quit' (or 'q') as the location to exit.

Starting location: Manila, PH
Destination:       Quezon City, PH

╭─────────────── Trip Summary ───────────────╮
│              From  Manila, Philippines     │
│                To  Quezon City, Philippines│
│        Travel mode  Car (driving)          │
│      Trip duration  00:27:41               │
│ Distance (Kilometers)  15.83 km            │
│ Fuel used (Liters est.)  1.27 L            │
╰────────────────────────────────────────────╯

────────────── Turn-by-Turn Directions ──────────────
  #  Instruction                                      km
  1  Continue west on Rizal St...                   2.17
  2  Turn right onto Quezon Ave...                  0.93
  ...
```

followed by a numbered turn-by-turn table. Type `quit` or `q` as a
location to exit; press `Ctrl+C` anywhere to leave politely.

Good sample inputs: `Manila, PH` -> `Quezon City, PH`,
`Cebu City, PH` -> `Mandaue City, PH`.

## GUI

The same directions are also available in a desktop window built with
Python's built-in `tkinter` - no extra install:

```
py gui.py
```

Enter a starting location and destination, pick metric/imperial units
and car/bike/walk, then press **Find route** (or Enter). The window
shows the resolved places, travel mode, duration, distance, the fuel
estimate for driving, and numbered turn-by-turn directions; requests
run in the background so the window stays responsive, and failures
appear as readable error text, never a traceback.

The GUI reuses the same API key setup as the CLI: the `GRAPHOPPER_KEY`
environment variable or `config.ini` (see [API key setup](#api-key-setup-required-free-no-credit-card)).
With no key configured the window shows the same setup instructions
instead of a crash, and picks the key up as soon as you add one.

Platform note: `tkinter` ships with the [python.org](https://www.python.org/downloads/)
Windows installer, but is missing from some Microsoft Store and
minimal Python installs. Check with:

```
py -c "import tkinter; print(tkinter.TkVersion)"
```

If that fails, reinstall Python from python.org with the *tcl/tk and
IDLE* option enabled.

## Browser app

The same directions are also served as a local web page by Flask:

```
py app.py
```

This starts a development server bound to `127.0.0.1:5000` (localhost
only - never exposed to other devices) and opens
<http://127.0.0.1:5000> in your default browser. Enter a starting
location and destination, pick metric/imperial units and car/bike/walk,
and submit; the page shows the resolved places, travel mode, duration,
distance, the fuel estimate for driving, and numbered turn-by-turn
directions. The form keeps what you typed, and every failure - empty
locations, unknown places, network problems, a missing or invalid key,
even an unexpected server error - appears as a readable message, never
a traceback.

The page works with JavaScript disabled (the form is a plain POST);
`static/app.js` only disables the button and shows "Searching..." while
the server responds.

The browser app reuses the same API key setup as the CLI and GUI: the
`GRAPHOPPER_KEY` environment variable or `config.ini` (see
[API key setup](#api-key-setup-required-free-no-credit-card)). With no
key configured the page shows the same setup instructions instead of a
crash, and you can add a key and resubmit without restarting the
server. The key never appears in any page or URL.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Web entry point: Flask routes (`GET /`, `POST /route`), 404/500 pages, `py app.py` launcher |
| `main.py` | CLI entry point: startup prompts, input loop, quit handling |
| `gui.py` | GUI entry point: tkinter window, background requests, rendering |
| `backend/config.py` | Loads the API key (env var `GRAPHOPPER_KEY`, then `config.ini`) |
| `backend/api.py` | Geocoding + routing calls; converts every failure into a plain result dictionary |
| `backend/services.py` | Web service layer: input validation, key resolution, route-to-template shaping |
| `backend/formatting.py` | Presentation-neutral formatting shared by all frontends (units, duration, fuel) |
| `templates/index.html` | The single server-rendered page (form, setup banner, errors, results) |
| `static/style.css`, `static/app.js` | Styling and the submit-button enhancement |
| `display.py` | CLI output: rich tables/panels over the shared formatters |
| `config.sample.ini` | Template for the git-ignored `config.ini` |
| `requirements.txt` | Third-party dependencies |
| `tests/` | unittest suites (CLI/GUI) + pytest tests (services, Flask routes); mocked network |
| `docs/` | Project deliverables 1-3 (selection, roles, workload) |

## Error handling reference

| Situation | What the user sees |
|---|---|
| No internet / DNS failure | Red panel: "No network connection" |
| API slower than 10 s | Red panel: "The request timed out" |
| Invalid API key (HTTP 401/403) | Red panel: how to fix the key |
| Unknown place name | Red panel: "Location not found" with a suggestion |
| API error message | The API's own message in a red panel |
| No key configured | Setup instructions at startup, app exits cleanly |
| `Ctrl+C` or `quit` | "Goodbye!" and a clean exit |

The GUI shows the equivalent messages as red text in the results area;
the browser app shows them as a red alert box on the page. In both,
empty locations are rejected before any request, API failures show the
same title/detail as the CLI's panels, a missing key shows the setup
instructions, and unexpected errors are displayed instead of crashing.
Unknown URLs get a friendly 404 page, and unhandled server errors are
logged to the console and rendered as a generic "Something went wrong"
page - never a traceback.

## Future enhancements (backlog)

Kept deliberately out of scope for this sprint; tracked for Project
Activity 4 (details in `docs/03-workload-status.md`):

1. Show resolved coordinates for each location
2. Save a trip report to a text/JSON file
3. Elevation along the route (GraphHopper returns it with `elevation=true`)
4. Multi-point routes (more than two stops)
5. Command-line arguments (`argparse`) for non-interactive use
6. Alternative routes (GraphHopper `alternative_routes` parameter)
7. Auto-detect units from the system locale
8. ~~Unit tests with a mocked API~~ - done: `tests/` now covers config,
   formatting, GUI logic, the worker handoff and the CLI entry, using
   the stdlib `unittest` runner (`py -m unittest discover -s tests -t .`)
9. Cache identical route requests to save API quota
10. ~~Web front-end (Flask) reusing `api.py`~~ - done: `py app.py` serves
    the browser app (see [Browser app](#browser-app))

## Future: packaging as a Windows executable (PyInstaller)

Nothing is packaged yet - the launch command is `py app.py`. If a
no-Python-installed machine ever needs to run the browser app, build a
single-file executable with [PyInstaller](https://pyinstaller.org/):

```
py -m pip install pyinstaller
py -m PyInstaller --onefile app.py --add-data "templates;templates" --add-data "static;static"
```

(The `;` separator is Windows-specific; use `:` on macOS/Linux.) The
`backend` package is collected automatically because `app.py` imports
it. The generated `dist/app.exe` starts the same localhost server and
opens the browser; templates and static assets resolve from the bundle.
Committing generated binaries is out of scope for this sprint.

## Contributing / continuation guide

Our team workflow: each member works on a branch, opens a pull request,
and another member reviews before merging into `main`.

To add a feature, touch the module that owns that concern:

- New prompt or input rule -> `main.py`
- New API parameter or endpoint -> `backend/api.py` (keep failures as
  `{"ok": False, ...}` dictionaries so display stays simple)
- New output/tables/columns -> `display.py` (Rich rendering); shared
  number/unit formatting -> `backend/formatting.py` (used by CLI, GUI
  and web)
- New GUI widget or behavior -> `gui.py`
- New web validation or route shaping -> `backend/services.py`
- New HTTP route or page element -> `app.py` + `templates/`
- New configuration -> `backend/config.py`

Keep the layers separate: `backend/api.py` never prints, `display.py`,
`gui.py` and `app.py` never call the network, and no frontend imports
another. That is what makes the app easy to extend and test.
