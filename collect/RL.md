# Collect Reinforcement Learning

This guide concentrates on how reinforcement learning plugs into Collect’s mechanics. It assumes familiarity with RL tooling and focuses on the environment that the game exposes to agents.

## Environment Snapshot

- **Agents** – Six players act simultaneously each tick. Player one can be switched to human control while the remaining five continue under AI control (or vice-versa).
- **Observation** – Each agent receives an `Observation` object containing:
  - Normalized player, resource, and target positions
  - Relative offsets from the player to the nearest resource (always) and to the delivery target (when carrying)
  - Binary flag indicating whether the player currently holds a resource
  - Player score (float)
  - Full tuple of all fifteen active resource coordinates for richer planners
- **Action space** – Nine discrete moves: `stay` plus the eight neighboring directions. Controllers may also emit a `(dx, dy)` pair with components in `{-1, 0, 1}`; the game maps that pair to the corresponding action.
- **Episode length** – A round lasts up to 24 hours of real time. After the round (or if the user ends it early), the environment resets following a 10-second intermission.
- **Randomization** – Player positions and resource placements are randomized at the start of every round, while the delivery target remains fixed at the center cell `(100, 100)`.

## Rewards and Dynamics

- **Delivery** – Delivering a held resource to any adjacent (including diagonal) cell around the target yields `+1` reward and immediately respawns that single resource at a fresh random location, keeping the total at fifteen.
- **Shaping feedback** – Each tick awards `+SHAPING_REWARD` (defaults to `+0.1`) when the Manhattan distance to the current objective shrinks and `-SHAPING_REWARD` (`-0.1`) otherwise. When empty-handed the objective is the nearest resource; when carrying a resource it is the closest target-adjacent cell.
- **Collision handling** – Attempting to move into another player blocks movement. The configurable `COLLISION_PENALTY` is currently `0.0`, but collisions still drop any carried resource, forcing the player to restart the pickup-delivery loop.
- **No decay** – Scores accrue only through deliveries. There are no time-based penalties or reward discounting inside the environment; wasted movement simply reduces the number of delivery opportunities.

State transitions obey straightforward rules:

1. Moves that leave the 200×200 field are ignored (player stays in place).
2. Only one entity occupies a cell at a time; blocked moves trigger the collision behaviour above.
3. Entering a resource cell removes that resource from the field and marks the player as holding it.
4. Delivery happens automatically whenever a holding player ends a tick adjacent to the target.
5. At round reset, all players return to new random positions with scores cleared; controller assignments persist.

## Controller Integration

- **Default AI** – `AIController` now builds a shared `CollectPufferAgent` (see `collect.puffer_agent`) whenever `pufferlib`, `torch`, and `gymnasium` are available. The agent wraps `pufferlib.models.Default`, samples discrete actions with a categorical policy, and applies lightweight policy/value updates on every reward signal. All AI-controlled players share the same instance so collected experience amortises across the team.
- **Fallback learner** – If the PufferLib toolchain is missing or fails to initialise, `AIController` falls back to the in-repo `NeuralPolicyAgent`, a single-hidden-layer policy-gradient learner that explores with ε-greedy sampling (ε starts near 0.8 and decays slowly to keep some exploration alive).
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

