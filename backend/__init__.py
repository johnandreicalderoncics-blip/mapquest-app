"""Shared backend package for the Directions app.

Contains the layers every frontend shares:
  api.py         - GraphHopper HTTP calls
  config.py      - API-key loading
  formatting.py  - presentation-neutral number/unit formatting
  services.py    - input validation and route orchestration (web layer)

Deliberately no re-exports here: importing backend.api pulls in
requests, and package-level imports would drag network code into every
consumer (including the tkinter GUI) even when it only needs config.
"""
