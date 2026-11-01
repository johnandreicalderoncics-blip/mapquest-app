# Deliverable 3 - Project Workload and Status

**Project Activity 3 - DEVASC**
**Team:** John Andrei Calderon, Sofia Beatriz Estioco, Ken Gultiano, Lawrence Ng (Scrum Leader)
**Sprint window:** October 25-27, 2026 (presentation October 28)

## Our strategy

Because our window is essentially one working day, we organized the
project as a **single short sprint with always-runnable increments**:
after every task the application still runs, and each completed feature
is committed to its own branch and merged by pull request. We divided
the work by module - configuration, API layer, display layer, error
handling - so members can work in parallel without touching the same
files. Task status is tracked in the table below (mirrored in a shared
Google Sheet the Scrum Leader maintains) and every member posts a short
update in the group chat when they finish or get blocked. The deadline
risk is managed by priority order: the features marked **High** are the
committed scope, and the stretch item is cut first if we fall behind.

## Task list, priority and status

| # | Task | Owner | Priority | Status |
|---|---|---|---|---|
| 1 | Project selection + rationale (Deliverable 1) | All (facilitated by Lawrence) | High | Done |
| 2 | Team roles and skillsets (Deliverable 2) | Lawrence | High | Done |
| 3 | Repository setup: repo, collaborators, `.gitignore`, `requirements.txt` | John Andrei | High | In progress |
| 4 | Baseline: recreate lab 4.9.2 code, config for the API key | John Andrei | High | Done |
| 5 | API layer: geocoding + routing + robust error handling | Ken | High | Done |
| 6 | Display layer: colored tables/panels with `rich` | Sofia | High | Done |
| 7 | Metric/imperial unit selection | John Andrei | High | Done |
| 8 | Travel mode selection (car/bike/walk) + geocoding | John Andrei | Medium | Done |
| 9 | README: setup, usage, error reference, continuation guide | Lawrence + Sofia | High | Done |
| 10 | Verification matrix: real routes, bad inputs, no key, Ctrl+C | Ken + All | High | In progress |
| 11 | Final presentation (slides + demo script) | Lawrence + All | High | To do (due Oct 28) |
| 12 | Backlog list for Project Activity 4 | Ken | Medium | Done |

## Workload expectations

Each member has other classes and commitments this week, so we agreed
on roughly **3-4 focused hours each inside the sprint window**, with
the Scrum Leader re-checking progress twice a day and reassigning
tasks if anyone is blocked. The module split (task 3-8) means no task
waits on another except the baseline (task 4), which unblocks
everything else.

## Definition of done

A task is **Done** only when: the code runs on the owner's machine, a
teammate has reviewed the pull request, and the feature appears in the
verification matrix with a passing result.

## Backlog for Project Activity 4 (future enhancements)

1. Show resolved coordinates for each location
2. Save a trip report to a text/JSON file
3. Elevation profile along the route (GraphHopper `elevation=true`)
4. Multi-point routes (more than two stops)
5. Command-line arguments (`argparse`) for non-interactive use
6. Alternative routes (GraphHopper `alternative_routes` parameter)
7. Auto-detect units from the system locale
8. Unit tests with `pytest` and a mocked API
9. Cache identical route requests to save API quota
10. Web front-end (Flask) reusing `api.py`
