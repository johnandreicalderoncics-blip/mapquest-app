# Deliverable 1 - Project Selection

**Project Activity 3 - DEVASC**
**Team:** John Andrei Calderon, Sofia Beatriz Estioco, Ken Gultiano, Lawrence Ng (Scrum Leader)
**Date:** October 26, 2026

## Our choice

We chose **Option 1: Feature Enhancements** - taking the working REST
API application from Cisco lab 4.9.2, *Integrate a REST API in a Python
Application*, and turning it into a more polished, more useful
directions tool.

**One change from the lab:** the original lab used the MapQuest API, but
MapQuest now requires billing/credit-card information even for its free
tier, which was not practical for our team. After comparing providers we
switched the API to **GraphHopper** (free key, no credit card), which
follows the exact same REST + JSON concepts the lab teaches: build an
HTTP request, parse the JSON response, handle status codes. The
application, its features and the learning outcomes are unchanged - only
the web service behind it is different.

## Why we chose it

1. **We build on proven code.** Every team member completed lab 4.9.2,
   so we start from a known-working baseline that already calls a
   directions REST API, parses the JSON, and prints directions.
   That drastically reduces technical risk under our one-sprint
   deadline.
2. **It matches the budget and time constraint.** Option 2 (a new IP
   address application) requires researching and evaluating unfamiliar
   APIs before writing any code. Option 1 lets us spend that time on
   real software-engineering practices: version control, code review,
   modular design and quality assurance.
3. **It demonstrates meaningful enhancement work.** The lab's output is
   plain `print()` text with hard-coded behavior. Our enhancements -
   colored table output, a metric/imperial unit choice, travel modes
   and robust error handling - are user-facing improvements that map
   directly to what the marketing department asked for, and they are
   the kind of work that differentiates teams in a real workplace.
4. **Familiar API concepts, professional practices.** Working with a
   REST/JSON directions API we already understand (GraphHopper mirrors
   MapQuest's request/response style) lets us focus on *how* we build
   (Git branches, pull requests, modular code) rather than *what* API
   to use - which is exactly what this project activity is grading.

## Features we commit to deliver

| # | Feature | Description |
|---|---|---|
| 1 | Colored, table-formatted output | Trip summary and turn-by-turn directions rendered as tables with colors using the `rich` library; errors as clear red panels instead of tracebacks |
| 2 | Metric / imperial units | User picks km/liters or miles/gallons at startup |
| 3 | Travel mode selection | Car, bicycle or walking routes (GraphHopper profiles) |
| 4 | Built-in geocoding | Users type place names, not coordinates; the app resolves them via the GraphHopper Geocoding API |
| 5 | Robust error handling | Friendly handling of no network, timeouts, invalid/missing API key, unknown places and Ctrl+C - the app never crashes with a traceback |

Future enhancements are tracked as backlog items in
[03-workload-status.md](03-workload-status.md) and in the repository
README, ready for Project Activity 4.
