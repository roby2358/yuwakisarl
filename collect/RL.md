# Collect Reinforcement Learning

This guide explains how reinforcement learning plugs into Collect’s mechanics. It assumes familiarity with RL tooling and focuses on the environment that the game exposes to agents.

## Environment Snapshot

- **Agents** – Six players act simultaneously each tick. Player one can be switched to human control while the remaining five continue under AI control (or vice versa).
- **Observation** – Each agent receives an `Observation` (length `Observation.vector_length() == 9`) composed of:
  - Normalised `(dx, dy)` offsets from the player to the nearest resource
  - Normalised `(dx, dy)` offsets from the player to the delivery target
  - Normalised `(dx, dy)` offsets from the player to the nearest other player
  - Normalised `(dx, dy)` offsets from the player to the roaming monster
  - Binary flag indicating whether the player currently holds a resource
- **Action space** – Nine discrete moves: `stay` plus the eight neighbouring directions. Controllers can also emit a `(dx, dy)` pair with components in `{-1, 0, 1}`; the game maps that pair to the corresponding action.
- **Episode cadence** – A round lasts up to 24 hours of real time. After the round (or if the user ends it early), the environment resets following a 10-second intermission while controller assignments persist.
- **Randomisation** – Player positions and resource placements are rerolled at the start of every round. The delivery target stays fixed at the centre cell `(100, 100)` and the monster begins at a random location.
- **Non-player entities** – A monster chases resource carriers with a stochastic policy (roughly 30% chance to move toward the closest carrier each tick). Getting closer to the monster incurs a shaping penalty; opening distance yields a small reward.

## Rewards and Dynamics

- **Delivery** – Delivering a held resource to any adjacent (including diagonal) cell around the target yields `+1` reward and immediately respawns that single resource at a fresh random location, keeping the total at fifteen.
- **Objective shaping** – Each tick awards a value between `-SHAPING_REWARD_MAX` and `+SHAPING_REWARD_MAX` (defaults clamp to ±1.0) based on the change in Manhattan distance to the current objective. When empty-handed the objective is the nearest resource; while carrying it is the closest target-adjacent cell.
- **Monster pressure** – Moving farther from the monster grants up to `+0.5`; moving closer costs up to `-0.5`. This bonus is additive with the primary shaping term.
- **Collision handling** – Attempting to move into another player blocks movement. The configurable `COLLISION_PENALTY` is currently `0.0`, but collisions still drop any carried resource, forcing the player to restart the pickup–delivery loop.
- **No environmental decay** – Scores accrue only through deliveries. There are no time-based penalties or environmental reward discounts; inefficient paths simply reduce the number of delivery opportunities before the round timer expires.

State transitions honour a few straightforward rules:

1. Moves that leave the 200×200 field are ignored (the player remains in place).
2. Only one entity occupies a cell at a time; blocked moves trigger the collision behaviour above.
3. Entering a resource cell removes that resource from the field and marks the player as carrying it.
4. Delivery happens automatically whenever a carrying player ends a tick adjacent to the target.
5. Round reset restores players to fresh random positions with zeroed scores; controller assignments remain unchanged.

## Controller Integration

- **Default AI** – Each `AIController` instance lazily constructs its own `CollectPufferAgent` (see `collect.puffer_agent`) when `torch`, `gymnasium`, and the optional `pufferlib` dependency import successfully. The policy is a widened three-layer MLP with GELU activations that samples actions from a categorical distribution and updates via an on-policy actor–critic step. Value targets bootstrap from the next observation using a configurable discount factor.
- **Fallback learner** – If the PufferLib stack is unavailable, the controller falls back to the built-in `NeuralPolicyAgent`, a multi-layer policy-gradient learner (three hidden layers by default) that explores with ε-greedy sampling. The agent tracks a running baseline and performs single-step REINFORCE-style updates.
- **Agent lifecycle** – Controllers do not share agents by default; every AI-controlled player maintains its own learner instance. If you want experience sharing, construct the controllers with a shared agent object or extend `AIController` accordingly.
- **Human override** – Pressing `Enter` toggles player one between human keyboard control (`Q W E A D Z X C`) and AI control without affecting the other players.

## Training Notes

- **Non-stationarity** – All six agents move concurrently, so the environment is highly non-stationary. Centralised critics, opponent modelling, or scripted sparring partners can stabilise learning.
- **Credit assignment** – Built-in agents optimise for immediate rewards (one-step bootstrapped returns for Puffer, single-step policy gradient for the neural agent). If your algorithm requires longer-horizon credit, extend the agents to retain short trajectories or integrate with your preferred RL library.
- **Exploration** – Rewards are sparse. Encourage exploration via epsilon-greedy schedules, entropy bonuses, curricula that simplify the task early on, or auxiliary distance-based rewards.
- **Episode handling** – Treat each round as an episode boundary. If your framework needs explicit terminal signals, watch for the `GameState.reset_round()` call or replicate the timing logic externally.
- **Observability** – The observation vector intentionally compresses the world into relative offsets. If you need richer context (scores, full resource map, time remaining, etc.), extend the `collect.types.Observation` dataclass and keep the vector length in sync.

## Extending the Environment

- Add or reorder observation features by modifying `collect.types.Observation` (and update any agents/tests that depend on `Observation.vector_length()`).
- Emit raw `(dx, dy)` vectors from custom controllers to leverage diagonal movement without enumerating action IDs.
- Override or wrap `GameState.update_player` to introduce alternative reward shaping, logging, or curriculum mechanics.
- Swap in alternative controllers by subclassing `AIController` or injecting your own policy objects that respect the `act(...)` / `learn(...)` interface used in the existing agents.