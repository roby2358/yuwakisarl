# MINIGAM

Quarter-backgammon prototype playable in the browser, served by a lightweight FastAPI backend and driven by rule-aware JavaScript logic.

## Overview

- Two-player race game: you face a random-move AI that always moves bar → 6 → 1 → bear off.
- Movement and hitting rules follow the MINIGAM specification (`MINIGAM.md`), with forced moves when at least one die is usable.
- Keyboard-first interface: space rolls your dice, digits `1-6` move or enter to that destination, and `b1-6` bears off from that point.
- UI renders a six-point board, bars, dice, and message log in cool, clear colors per the spec.

## Tech Stack

- FastAPI (Python) serving static assets; future hooks reserved for AI via WebSocket.
- Static frontend under `resources/public` built with HTML/CSS, jQuery, and vanilla JavaScript.
- Rule engine extracted to `game_logic.js` for reuse across browser code and Node tests.
- Testing:
  - Python backend tests with `pytest`.
  - Frontend/game-logic unit tests with Node’s built-in `node:test`.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (preferred) or `pip` for Python dependencies
- Node.js 20+ for JavaScript tests

## Installation

Using `uv` (recommended):

```bash
uv sync
```

This creates a virtual environment and installs the Python dependencies declared in `pyproject.toml`.

If you prefer `pip`:

```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r <(uv pip compile pyproject.toml)  # or manually install fastapi uvicorn pytest httpx
```

Install Node dependencies (none required beyond the standard library), but ensure Node 20+ is available for tests.

## Running the App

Start the FastAPI server with uvicorn:

```bash
uv run uvicorn app.main:app --reload
```

Then navigate to `http://127.0.0.1:8000/` to play. The server currently serves static files only; gameplay runs entirely client-side.

## Controls

- `Space`: Roll dice at the start of your turn or end the turn if all dice are used.
- `1-6`: Move/enter to that destination point. If you have checkers on the bar, the appropriate die must be available.
- `b1-6`: Bear a checker off from that point (requires exact die, no checkers behind, and empty bar).

## Testing

Python backend tests:

```bash
uv run pytest
```

JavaScript rule-engine tests:

```bash
node --test tests/js/test_game_logic.js
```

Run both suites regularly to ensure rule changes and server tweaks stay consistent.

## Project Structure

```
app/                    # FastAPI entrypoint
resources/public/       # Static frontend assets
tests/python/           # Backend unit tests (pytest)
tests/js/               # Game-logic unit tests (node:test)
MINIGAM.md              # Full game rules
SPEC.md                 # Technical and UI specification
```

