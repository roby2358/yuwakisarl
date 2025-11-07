# Collect Reinforcement Learning

This guide concentrates on how reinforcement learning plugs into Collect’s mechanics. It assumes familiarity with RL tooling and focuses on the environment that the game exposes to agents.

## Environment Snapshot

- **Agents** – Six players act simultaneously each tick. Player one can be switched to human control while the remaining five continue under AI control (or vice-versa).
- **Observation** – Each agent receives an `Observation` object containing:
  - Player position `(px, py)`
  - Target position `(tx, ty)`
  - Coordinates for the nearest resource `(rx, ry)` (derived from the active resource list)
  - Binary flag indicating whether the player currently holds a resource
  - Player score (float)
  - Full tuple of all ten active resource coordinates for richer planners
- **Action space** – Nine discrete moves: `stay` plus the eight neighboring directions. Controllers may also emit a `(dx, dy)` pair with components in `{-1, 0, 1}`; the game maps that pair to the corresponding action.
- **Episode length** – A round lasts up to 180 seconds of real time. After the round (or if the user ends it early), the environment resets following a 10-second intermission.
- **Randomization** – Player, target, and resource placements are randomized at the start of every round, ensuring diverse layouts.

## Rewards and Dynamics

- **Delivery** – Delivering a held resource to any adjacent (including diagonal) cell around the target yields `+1` reward and immediately respawns that single resource at a fresh random location, keeping the total at ten.
- **Collisions** – Attempting to step into another player’s cell blocks movement. If the moving player carried a resource, it is dropped and respawned randomly, introducing an implicit opportunity cost.
- **No penalties** – There are no time-based penalties, shaping rewards, or decay terms. Wasted movement simply reduces the number of delivery opportunities.

State transitions obey straightforward rules:

1. Moves that leave the 200×200 field are ignored (player stays in place).
2. Only one entity occupies a cell at a time; blocked moves trigger the collision behaviour above.
3. Entering a resource cell removes that resource from the field and marks the player as holding it.
4. Delivery happens automatically whenever a holding player ends a tick adjacent to the target.
5. At round reset, all players return to new random positions with scores cleared; controller assignments persist.

## Controller Integration

- **Default AI** – `AIController` forwards the observation to a `pufferfish_ai.Agent` if the dependency is present. Any integer 0–8 or `(dx, dy)` pair is mapped into the nine-direction action set.
- **Heuristic fallback** – When no learned agent is available, a deterministic policy heads toward the nearest resource and then aims for the closest target-adjacent cell once loaded.
- **Human override** – Pressing `Enter` toggles player one between human keyboard control (`Q W E A D Z X C`) and AI control without affecting other players.

## Training Notes

- **Non-stationarity** – All six agents move concurrently. Multi-agent training can benefit from centralized critics, population-based training, or training against scripted opponents.
- **Exploration** – Rewards are sparse. Encourage exploration through epsilon-greedy policies, entropy bonuses, shaped auxiliary rewards (e.g., negative distance to the nearest resource/target), or curriculum strategies that simplify the task early on.
- **Episode handling** – Treat the end-of-round reset as an episode boundary. If your framework needs explicit terminal signals, watch for the `GameState.reset_round()` call or replicate the timing logic externally.

## Extending the Environment

- Adjust `AIController._encode_observation` if your agent benefits from additional signals (other players’ positions, remaining time, etc.).
- Emit raw `(dx, dy)` vectors from custom controllers to leverage diagonal movement without enumerating action IDs.
- Implement reward shaping or logging hooks by wrapping `GameState.update_player` or subclassing `Game` to capture transitions before they’re applied.
- Swap in alternative controllers by subclassing `AIController` or constructing your own policy that consumes the `Observation` dataclass.

