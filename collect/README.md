# Collect

Collect is a real-time reinforcement learning playground built with pygame. Players (human or AI) move across a fixed 200×200 grid, gathering a resource and delivering it to a target for points. The project is designed for experimenting with controller strategies while keeping the core game loop simple and deterministic.

## Features
- Simultaneous real-time play with multiple players.
- Deterministic, testable game-state logic separated from rendering.
- Six active players per round; toggle player one between human and AI control at runtime.
- Optional keyboard control for player one; remaining players share a built-in neural policy (with relative-position features and tuned ε-greedy exploration) or use custom controllers.
- Default round spawns six players with fifteen resources distributed randomly across the grid and a fixed target at the center (100, 100).
- Built-in shaping reward now gives +0.1 for steps that reduce distance to the current objective and -0.1 otherwise, with a -1.0 penalty for colliding with another player (wall penalties currently disabled while we investigate behaviour).
- Pause/resume, round timing, collision penalties, and diagonal delivery scoring rules from `SPEC.md`.

## Requirements
- Python 3.10+
- `uv` for dependency management (recommended)

Game runtime dependencies:  
`pygame`

Development dependencies:  
`pytest`

## Setup
```bash
uv sync
```

This creates a `.venv` and installs the project plus dev dependencies.

## Running the Game
```bash
uv run collect-game
```

The `collect-game` script runs the same `collect.main:main` entry point defined in `pyproject.toml`, so no manual `PYTHONPATH` tweaks or editable installs are required—even on Windows shells such as PowerShell.

Controls while playing:
- `Enter` – toggle player one between AI and keyboard control.
- `Q / W / E / A / D / Z / X / C` – move to any of the eight neighboring cells (diagonals included).
- `Space` – pause or resume the round.
- `Esc` (once) – end the current round early.
- `Esc` (twice) – exit the game.

Rounds last 24 hours with a ten-second break before the next round starts, giving on-policy learners plenty of experience per episode.

## Tests
```bash
uv run pytest
```

Tests cover the pure `GameState` logic, ensuring resource collection, delivery, and collision behaviour remain correct.

## Extending AI Control
The default AI controller uses a heuristic pathing strategy. To integrate a different agent, update or replace `collect/ai_controller.py` so that `select_action` chooses actions based on the provided `Observation`.

If you prefer to invoke the module directly, you can run:

```powershell
$env:PYTHONPATH="src"
uv run python -m collect.main
Remove-Item Env:PYTHONPATH
```

The environment variable ensures the `src` layout remains discoverable without needing an editable install.

## Licensing
See `SPEC.md` for original specification details and project requirements. If you plan to distribute the game, ensure any new assets or libraries comply with their respective licenses.

