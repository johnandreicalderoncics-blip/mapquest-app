# Directions Finder - Feature-Enhanced CLI (GraphHopper)

A Python command-line application that gets driving, cycling or walking
directions from the [GraphHopper Route API](https://docs.graphhopper.com/)
and displays them as colored, easy-to-read tables.

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

## Requirements

- Python 3.10 or newer
- The `requests` and `rich` packages:

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

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Entry point: startup prompts, input loop, quit handling |
| `config.py` | Loads the API key (env var `GRAPHOPPER_KEY`, then `config.ini`) |
| `api.py` | Geocoding + routing calls; converts every failure into a plain result dictionary |
| `display.py` | All output: rich tables/panels, unit-aware formatting |
| `config.sample.ini` | Template for the git-ignored `config.ini` |
| `requirements.txt` | Third-party dependencies |
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
8. Unit tests with `pytest` and a mocked API
9. Cache identical route requests to save API quota
10. Web front-end (Flask) reusing `api.py`

## Contributing / continuation guide

Our team workflow: each member works on a branch, opens a pull request,
and another member reviews before merging into `main`.

To add a feature, touch the module that owns that concern:

- New prompt or input rule -> `main.py`
- New API parameter or endpoint -> `api.py` (keep failures as
  `{"ok": False, ...}` dictionaries so display stays simple)
- New output/tables/columns -> `display.py` (unit labels and the fuel
  estimate live there)
- New configuration -> `config.py`

Keep the layers separate: `api.py` never prints, `display.py` never
calls the network, and `main.py` only orchestrates. That is what makes
the app easy to extend and test.
