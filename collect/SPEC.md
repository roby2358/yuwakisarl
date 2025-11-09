# Collect Technical Specification

This is a reinforcement learning experiment called "Collect".

# Tech stack
- python
- uv
- pygame
- PufferLib AI Reinforcement Learning Framework

## Overview
- MUST ship a real-time resource collection game whose entry point is `collect.main:main`.
- MUST keep the game logic deterministic within `collect.game_state.GameState`, isolating rendering and I/O side effects inside `collect.game`.
- MUST support simultaneous play for multiple agents sharing a single board state.
- SHOULD keep the implementation modular so controllers, rendering, and configuration can evolve independently.

## Field And Objectives
- MUST fix the board size to 200×200 cells, defined once in `collect.config.FIELD_DIMENSIONS`.
- MUST draw each cell at `collect.config.CELL_SIZE_PX` pixels (currently 4) and reuse the pre-rendered grid background each frame.
- MUST spawn exactly one delivery target at the grid centre `(100, 100)` and treat all eight neighbouring cells as valid delivery spots.
- MUST maintain `collect.config.RESOURCE_COUNT` (default 15) active resources by respawning after pickup or drop.
- MUST keep resource placement off occupied cells, outside the target exclusion zone (target + neighbours), and without duplicates.
- SHOULD randomise placements using `_random_cell` while failing fast with a `RuntimeError` if the field fills.

## Players And Controllers
- MUST initialise `DEFAULT_PLAYER_COUNT` (6) players identified by indices `0..n-1`, each starting with score `0` and no resource.
- MUST prevent multiple players from occupying the same cell; attempted moves into an occupied cell leave the mover in place and trigger collision handling.
- MUST toggle player `0` between AI and keyboard control via `Enter`, leaving other players AI-controlled.
- MUST map keyboard input `QWE/AD/ZXC` to the eight movement actions and fall back to `STAY` when no relevant key is held.
- SHOULD store controller type per player inside `GameState` so human/AI toggles persist through resets.

## Movement And Scoring
- MUST expose nine discrete actions (`STAY` plus eight directions) from `collect.types.Action`, each mapped to a unit delta.
- MUST ignore moves that leave the board; the player remains in place and receives no penalty.
- MUST restrict players carrying a resource from collecting a second resource; attempted pickups simply fail and the player stays put.
- MUST deliver a carried resource when the player ends a tick in any cell adjacent (including diagonals) to the target, incrementing score by one.
- MUST respawn a delivered or dropped resource immediately to maintain the target count.
- SHOULD ensure collision handling removes the carried resource, respawns it elsewhere, and adds `COLLISION_PENALTY` (currently 0.0) to that tick’s reward value.

## Rewards And Feedback
- MUST compute per-tick reward as the sum of scoring delta, collision penalty, and the shaping value produced by `_shaping_reward`.
- MUST scale shaping rewards between `SHAPING_REWARD_MIN` (0.1) and `SHAPING_REWARD_MAX` (1.0) based on Manhattan distance progress toward the active goal (nearest resource or target).
- SHOULD return zero shaping reward when distance information is unavailable (no resources found).
- SHOULD keep all reward calculations deterministic for identical random seeds and action sequences.

## Round Flow And Timing
- MUST tick the game loop at `FRAME_RATE` (30 FPS) using `pygame.time.Clock`.
- MUST time each round to `ROUND_SECONDS` (24 hours) and follow it with a `ROUND_BREAK_SECONDS` (10 seconds) intermission before resetting.
- MUST support `Space` to pause/resume the active round without advancing game state.
- MUST interpret a single `Esc` press as ending the current round and a second consecutive `Esc` as terminating the program.
- SHOULD redraw the board while paused, overlaying HUD text indicating state, remaining time, and scores.

## AI Controllers
- MUST provide one `AIController` instance per player that accepts `collect.types.Observation` snapshots each tick.
- MUST encode observations to a 14-element feature vector capturing player, target, resource, and nearest-player offsets before passing to the agent.
- MUST support optional `CollectPufferAgent` integration; when unavailable, `AIController` falls back to the built-in `NeuralPolicyAgent` and logs the choice.
- MUST ensure each controller owns its own agent instance so learning traces remain player-specific.
- SHOULD support agents whose `act`/`learn` signatures optionally accept an `actor_id`, handling both cases gracefully.

## Rendering
- MUST render players as filled circles using `PLAYER_COLOR`, overlay a smaller `RESOURCE_COLOR` circle when the player carries a resource, and draw standalone resources as filled circles.
- MUST draw the target as an outlined circle at its cell centre using `TARGET_COLOR`.
- MUST render HUD text in `TEXT_COLOR` with the current pause state, remaining seconds (clamped ≥0), and per-player scores.
- SHOULD avoid reallocating surfaces inside the render loop by caching the grid surface during `Renderer` initialisation.

## Configuration And Packaging
- MUST centralise all modifiable constants in `collect.config` for reuse by runtime and tests.
- MUST expose the package as `collect` under `src/` and register the console script `collect-game` in `pyproject.toml`.
- SHOULD keep configuration values simple primitives or frozen dataclasses to discourage in-place mutation.

## Testing
- MUST keep executable tests under `tests/`, using `pytest` to cover core logic such as resource placement, collisions, deliveries, and shaping rewards.
- MUST control randomness in tests by monkeypatching `_random_cell` or related helpers so expectations remain deterministic.
- SHOULD gate optional-dependency tests (`torch`, `pufferlib`, etc.) behind `pytest.importorskip` to keep the base test suite reliable.

## Dependencies
- MUST require Python 3.10+ and depend on `pygame` for runtime rendering/input.
- SHOULD manage dependencies via `uv` with metadata captured in `pyproject.toml` and `UV` lockfiles.
- SHOULD treat `torch`, `gymnasium`, and `pufferlib` as optional extras used only when the puffer-based agent is active.
