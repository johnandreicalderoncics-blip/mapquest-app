# Claude Code Prompt: Build a Browser Frontend

You are working in the `mapquest-app` Python repository. Build a browser-based
frontend while preserving the pre-existing CLI and application behavior.

## Goal

Add a local web frontend. The Python application should start a local web
server, open the user's default browser, and provide a form for entering an
origin and destination, choosing units and a travel mode, requesting a route,
and viewing the route summary and turn-by-turn directions.

The preferred implementation is a small Flask application launched by a new
`web_app.py` entry point. If a standalone executable is also desired, package
the application later with PyInstaller so the executable starts the local
server and opens the browser. Do not make the executable itself the frontend.

## Existing architecture

- `main.py` is the interactive CLI entry point. Do not replace or rewrite it.
- `api.py` contains GraphHopper geocoding and routing calls.
- `config.py` loads the API key from `GRAPHOPPER_KEY` or the local
  git-ignored `config.ini`.
- `display.py` contains Rich terminal rendering and must remain CLI-focused.
- `requirements.txt` contains the existing runtime dependencies.

## Required implementation

1. Create a separate web entry point such as `web_app.py`.
2. Reuse `config.get_api_key()` for API-key loading.
3. Reuse `api.fetch_route(key, origin, destination, units, profile)` for
   route retrieval.
4. Do not call `main.main()` from the web application.
5. Do not call Rich rendering functions from the web application.
6. Add a browser-facing route such as `GET /` and a form submission route
   such as `POST /route`.
7. Add HTML templates and CSS in a conventional `templates/` and `static/`
   structure. Keep presentation code separate from `api.py`.
8. Validate that both locations are non-empty before making a request.
9. Handle the existing result contract:
    - success: `{"ok": True, "data": ..., "from_name": ..., "to_name": ...}`
    - failure: `{"ok": False, "title": ..., "detail": ...}`
10. Render at least:
    - resolved origin and destination
    - travel mode
    - formatted duration
    - formatted distance
    - estimated fuel for driving routes
    - numbered turn-by-turn instructions
11. Handle missing API-key configuration with a clear web error instead of an
    unhandled traceback. If `config.get_api_key()` exits the process, refactor
    configuration handling carefully so the CLI's existing behavior remains
    unchanged and the GUI can display the setup message.
12. Handle unexpected request failures with a user-facing error page.
13. Keep the implementation typed and consistent with the existing code style.
14. Do not add a database, SPA framework, or unnecessary JavaScript.
15. Do not expose, hard-code, log, or commit the GraphHopper API key.
16. Add a local launcher that opens the default browser only when explicitly
    requested, or document the command to open the URL manually.

## Compatibility requirements

- `py main.py` must continue to launch the existing CLI.
- Existing `api.py`, `display.py`, and CLI output behavior must remain intact
  unless a narrowly scoped shared fix is required.
- Do not move or rename existing modules.
- Do not change the GraphHopper API contract.
- Add Flask to `requirements.txt` only if Flask is used.
- Keep the web server bound to localhost by default for local use.
- Do not assume that a packaged executable has access to files through the
  current working directory. Resolve templates and static assets reliably.
- If packaging is requested, use a separate PyInstaller configuration or
  documented command. Do not commit generated binaries unless explicitly
  requested.

## Testing requirements

Add focused tests where practical, especially for GUI-independent formatting
or result transformation logic. At minimum, verify:

- empty locations are rejected without an API call;
- successful route results are rendered in the browser;
- API failure dictionaries are rendered as user-facing errors;
- the CLI still imports and runs its existing entry point;
- the web route does not expose the API key;
- the server can be started locally without changing CLI behavior.

Use mocks for network calls. Do not make real GraphHopper requests in tests.

## Documentation requirements

Update the project README with:

- the new web frontend launch command;
- the GUI's purpose and local URL;
- the fact that the CLI remains available through `py main.py`;
- optional PyInstaller packaging and executable-launch instructions, if
  implemented.

At the end, report:

1. files changed;
2. how the GUI flow works;
3. tests run and their results;
4. any platform limitations or follow-up work.
