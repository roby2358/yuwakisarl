# Collect Reinforcement Learning Notes

This document describes how reinforcement learning fits into the Collect game. The focus here is on the game-specific dynamics, not on RL theory in general.

## Environment

- **Observation space** – Each agent receives a compact view of the world:
  - Player position `(px, py)`
  - Nearest resource position `(rx, ry)` computed from the list of active resources
  - Target position `(tx, ty)`
  - Binary flag for whether the player currently holds the resource
  - Player score (as a float)
- **Resource list** – The observation object also carries the full tuple of resource coordinates so custom controllers can reason about all ten resources simultaneously.
- **Population** – Six players act each tick. Human control can replace player one, but the remaining five players are AI-driven unless reassigned.
- **Action space** – Discrete with five options: `stay`, `move_up`, `move_down`, `move_left`, `move_right`.
- **Episode structure** – A round lasts up to 180 seconds of real time. The environment automatically resets after each round (or when the user ends the round early). Between rounds there is a 10 second break; the next round starts with fresh placements and scores reset to zero.

## Rewards

- Delivering a resource to any cell adjacent (including diagonals) to the target yields a reward of `+1` and immediately respawns that resource elsewhere on the field.
- Colliding with another player while holding the resource causes the agent to drop it. There is no direct penalty, but the resource respawns at a random location, creating an implicit cost in lost progress.
- There are no negative time penalties or decay terms. Deliberate stalling or repeated collisions simply wastes time that could have generated more positive rewards.

## State Transition Rules

1. **Movement** – Actions that would move a player off the 200×200 grid are ignored, leaving the player in place.
2. **Cell occupancy** – Only one entity may occupy a cell. Attempting to move into an occupied cell prevents movement. If the moving player was carrying the resource, the resource is dropped and respawned elsewhere on the field.
3. **Resource pickup** – When a player enters a resource cell, that resource is removed from the field and is considered “held” until delivery or a collision drop.
4. **Delivery** – If the player is holding a resource and moves adjacent (including diagonals) to the target, delivery happens automatically at the end of that tick, awarding the reward and respawning that single resource at a new random location (maintaining the total of ten).
5. **Round reset** – When a round ends, all players are repositioned randomly, scores are cleared, and a new resource/target placement is generated. Controller assignments (human vs. AI) persist across rounds.

## Controller Integration

- The default AI controller (`src/collect/ai_controller.py`) provides the observation vector to a `pufferfish_ai.Agent` if available. The returned integer action (0–4) is mapped into the game’s discrete action set.
- When the Pufferfish dependency is missing, a deterministic heuristic policy acts as a fallback. The heuristic moves toward the resource when empty-handed, or toward the closest target-adjacent cell when carrying.
- Human control can take over player one at runtime via the `Enter` key. This toggles the controller type but does not affect other agents.

## Training Considerations

- **Episode boundaries** – Each 180-second round is a natural episode. Agents can observe the game clock to learn timing (the renderer already exposes the clock to players, but the observation vector can be extended for agents if needed).
- **Randomization** – Starting positions for players, targets, and all ten resources are randomized every round, ensuring a diverse set of initial states and resource configurations.
- **Simultaneity** – All agents act on the same tick. Training multiple agents simultaneously introduces non-stationarity; consider training one agent at a time or using centralized training strategies for multi-agent RL.
- **Exploration** – Deliveries yield sparse rewards. Exploration strategies (epsilon-greedy, entropy bonuses, curriculum) may be needed for agents to reliably learn the pickup-and-delivery cycle.

## Extensibility

- Modify the observation encoder in `AIController._encode_observation` to include more features (e.g., distances to all resources or opponent locations) if the learning algorithm benefits from a richer state.
- Add shaped rewards (e.g., distance to resource/target) by adjusting `GameState` to emit reward events or by wrapping the environment with a shaping layer.
- For custom agents, replace or subclass `AIController` and use the `Observation` dataclass defined in `src/collect/types.py` for a structured view of the state.

