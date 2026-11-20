# Project Activity 4 - Automated Testing & CI/CD

Repository: https://github.com/johnandreicalderoncics-blip/mapquest-app

> Sections marked **[Team: personalize]** are drafts based on the repo
> history. Edit them so they reflect what actually happened in your team.

---

## 1. Backlog features implemented

| # | Feature | Where in code |
|---|---|---|
| 1 | **Desktop GUI** (tkinter) for route lookup | `src/frontend/desktop/gui.py`, `run_gui.py` |
| 2 | **Interactive OpenStreetMap view** showing the route line and markers | `src/frontend/desktop/map_widget.py` (tkintermapview) |
| 3 | **Browser-based Directions Finder** (Flask web app with themes, toasts, loading states) | `src/frontend/web/app.py`, `templates/`, `static/` |
| 4 | **Automated testing + CI pipeline** (this activity) | `tests/`, `.github/workflows/ci.yml` |

### Objectives
- **GUI** - let non-technical users get directions without a terminal.
- **OpenStreetMap** - show the route visually, not just as a table of steps.
- **Web Directions Finder** - reach users on any device with a browser; no install.
- **CI pipeline** - catch broken code automatically on every commit, before it is merged or deployed.

### Why these features were chosen
- Marketing feedback asked for a friendlier interface than the CLI.
- All three front-ends reuse the same `backend/` (API, services, formatting), so
  new features were cheap to add without rewriting core logic.
- More front-ends meant more ways for one teammate's change to break another's
  - which is exactly the problem the CI pipeline solves.

## 2. Team roles, knowledge and skillsets

| Member | Role (PA4) | Skills used / gained |
|---|---|---|
| John Andrei Calderon | Developer, repo owner, **CI/CD owner** | Python, Git/GitHub, GitHub Actions, branch protection |
| Sofia Beatriz Estioco | Developer - UI (GUI + web) | tkinter, HTML/CSS/JS, Flask templates |
| Ken Gultiano | **QA / test lead** | pytest, mocking (`unittest.mock`), test design |
| Lawrence Ng | Scrum Leader, documentation | Sprint tracking, presentation, reviewing PRs |

**What changed:** Ken's QA role moved from manual checks to writing automated
pytest cases; John took ownership of the pipeline config. **[Team: personalize]**

## 3. Team strategy (what changed)

- **Feature branches + Pull Requests only.** Nobody pushes directly to `main`.
- **Every push triggers CI.** GitHub Actions runs lint + the full test suite.
- **Merge gate.** `main` has a branch-protection rule: the CI checks must be
  green *and* one teammate must approve before the Merge button unlocks.
- **Tests travel with features.** A PR that adds a feature must add tests for it.
- **API is mocked in tests**, so CI needs no secret key and never hits rate limits.

---

## 4. Automated testing process (design)

```
 developer ──push──▶ GitHub ──triggers──▶ GitHub Actions
                                            │
                     ┌──────────────────────┴───────────────────┐
                     │ Job 1: Lint (flake8: syntax/undefined names) │
                     └──────────────────────┬───────────────────┘
                                            │ only if lint passes
           ┌────────────────────────────────┼────────────────────────────┐
     Tests on Py 3.10              Tests on Py 3.11              Tests on Py 3.12
     (xvfb for tkinter, pytest, coverage, JUnit report uploaded)
           └────────────────────────────────┼────────────────────────────┘
                                            ▼
                     ✅ all green → PR can be merged   ❌ any red → merge blocked
```

**Trigger rules** (`.github/workflows/ci.yml`):
- `push` to any branch - feedback on every commit.
- `pull_request` into `main` - the check that gates merging.
- `workflow_dispatch` - manual re-run button.

### Why GitHub Actions (vs Jenkins / CircleCI)

| | GitHub Actions | Jenkins | CircleCI |
|---|---|---|---|
| Hosting | Built into GitHub, free for public repos | Must run & maintain our own server | Hosted, separate account |
| Setup | One YAML file in repo | Server, plugins, webhooks, credentials | YAML + link GitHub app |
| PR status checks | Native | Via plugin | Via app |
| Fit for a 4-person student team | ✅ Best | Heavy | Good |

We chose GitHub Actions because it needs zero infrastructure and integrates
directly with branch protection. Jenkins was considered; it is more flexible
for on-prem/enterprise setups but requires a server we would have to host.

## 5. Test cases

**458 automated tests** across 38 files, all passing.

| Area | Example files | What they check |
|---|---|---|
| Backend API | `test_services.py`, `test_api_error_handling.py`, `test_services_error_handling.py` | Geocoding/routing requests, HTTP errors, timeouts, bad API key, no network |
| Config | `test_config.py`, `test_config_error_handling.py` | Reading/validating the API key and config file |
| Formatting | `test_formatting*.py` | Unit conversion (km/mi), fuel estimate, time formatting |
| CLI | `test_cli_entry.py`, `test_cli_error_handling.py` | Entry point and friendly error messages |
| Desktop GUI | `test_gui_logic.py`, `test_map_widget.py`, `test_thread_safety.py`, `test_worker.py`, `test_window_resize.py` | GUI logic, map markers/route, background threads |
| Web app | `test_app.py`, `test_coordinate_*.py` | Flask routes, JSON responses, coordinate validation |
| Web UI | `test_*_js.py`, `test_a11y_*.py`, `test_contrast.py`, `test_responsive_css.py` | JS controllers, accessibility, color contrast, responsive CSS |

Run locally:
```bash
pip install -r requirements.txt
python -m pytest -v
```

### Bug found by setting up CI
Three test files import `bs4` (BeautifulSoup), but it was **missing from
`requirements.txt`**. It worked on the machine where it happened to be
installed and failed everywhere else - exactly the "works on my machine"
problem CI exists to catch. Fixed by adding `beautifulsoup4` to requirements.

## 6. Enabling the merge gate (one-time, repo owner)

GitHub → repo **Settings → Branches → Add branch protection rule**:
1. Branch name pattern: `main`
2. ✅ Require a pull request before merging (1 approval)
3. ✅ Require status checks to pass → select `Lint (syntax + undefined names)`
   and the three `Tests (Python 3.x)` checks
4. ✅ Require branches to be up to date before merging
5. Save.

(Status checks only appear in that list after the workflow has run once.)

---

## 7. Presentation outline (video)

1. **Intro** (Lawrence) - team, goal of PA4.
2. **New features demo** (Sofia) - GUI, OpenStreetMap route, web app.
3. **Code pushed to GitHub** (John) - show branch, commits, open PR.
4. **Test cases** (Ken) - walk through a few tests; run `pytest` live.
5. **CI/CD pipeline** (John) - show `ci.yml`, the Actions tab running, then
   push a deliberately broken commit → red ❌ → Merge button blocked → fix → green ✅.
6. **Reflection** (all) - see below.

## 8. Reflection & team activities  **[Team: personalize]**

**Issues faced and solutions**
- Missing `bs4` dependency only surfaced on a clean environment → CI found it; added to requirements.
- tkinter GUI tests need a display, which CI servers don't have → used `xvfb-run` (virtual display).
- Tests must not depend on the real GraphHopper key → API calls are mocked, so no secrets in CI.
- Which CI tool? → compared Jenkins, CircleCI, GitHub Actions; picked Actions for zero setup.

**What we learned** - CI turns "did someone break it?" from a manual review
question into an automatic answer on every commit; tests are only useful if
they run on every change.

**What did you enjoy / what worked well?** - Shared backend meant each person
could own a front-end in parallel; PR reviews spread knowledge.

**Team problems and resolution** - e.g. merge conflicts when two people edited
the same file → smaller PRs, pull `main` often, agree on file ownership.

**Technical problems and resolution** - see "Issues faced" above.

**Accountability** - each task tracked with an owner by the Scrum Leader;
CI makes individual accountability visible (the red ❌ shows whose commit broke
the build); PR approval makes the team jointly responsible for `main`.

**Decision-making process** - proposals discussed in team meetings/chat; the
owner of an area decides details, larger choices (e.g. CI tool) by consensus,
Scrum Leader breaks ties.

**Team dynamics & lessons learned** - automating checks reduced friction in
reviews (less arguing about "it works for me"); write tests alongside code,
not after.
