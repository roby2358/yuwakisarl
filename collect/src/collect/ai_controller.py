"""AI controller integration with the Pufferfish framework."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from .config import FIELD_DIMENSIONS
from .types import Action, Observation

try:
    from pufferfish_ai import Agent as PufferfishAgent  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    PufferfishAgent = None  # type: ignore[misc]


@dataclass
class AIController:
    """Selects actions for an AI-controlled player."""

    player_identifier: int

    def __post_init__(self) -> None:
        self._agent = self._build_agent()

    def select_action(self, observation: Observation) -> Action:
        if self._agent is not None:
            agent_action = self._select_agent_action(observation)
            if agent_action is not None:
                return agent_action
        return self._heuristic_action(observation)

    def _build_agent(self) -> Optional["PufferfishAgent"]:
        if PufferfishAgent is None:
            return None
        return PufferfishAgent()

    def _select_agent_action(self, observation: Observation) -> Optional[Action]:
        agent = self._agent
        if agent is None:
            return None
        state_vector = self._encode_observation(observation)
        raw_action = agent.act(state_vector)  # type: ignore[attr-defined]
        return self._map_agent_action(raw_action)

    def _encode_observation(self, observation: Observation) -> Sequence[float]:
        player = observation.player
        px, py = player.position
        tx, ty = observation.target
        rx, ry = self._nearest_resource(player.position, observation.resources)
        has_resource = 1.0 if player.has_resource else 0.0
        score = float(player.score)
        return (float(px), float(py), float(rx), float(ry), float(tx), float(ty), has_resource, score)

    def _map_agent_action(self, raw_action: object) -> Optional[Action]:
        if isinstance(raw_action, int):
            mapping = {
                0: Action.STAY,
                1: Action.MOVE_UP,
                2: Action.MOVE_DOWN,
                3: Action.MOVE_LEFT,
                4: Action.MOVE_RIGHT,
                5: Action.MOVE_UP_LEFT,
                6: Action.MOVE_UP_RIGHT,
                7: Action.MOVE_DOWN_LEFT,
                8: Action.MOVE_DOWN_RIGHT,
            }
            return mapping.get(raw_action)
        if isinstance(raw_action, (tuple, list)) and len(raw_action) == 2:
            dx, dy = raw_action
            if isinstance(dx, (int, float)) and isinstance(dy, (int, float)):
                return Action.from_delta(int(dx), int(dy))
        return None

    def _heuristic_action(self, observation: Observation) -> Action:
        player = observation.player
        if player.has_resource:
            target_cell = self._nearest_adjacent_cell(player.position, observation.target)
            return self._step_towards(player.position, target_cell)
        nearest_resource = self._nearest_resource(player.position, observation.resources)
        return self._step_towards(player.position, nearest_resource)

    def _step_towards(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Action:
        sx, sy = start
        gx, gy = goal
        delta_x = gx - sx
        delta_y = gy - sy
        if delta_x == 0 and delta_y == 0:
            return Action.STAY
        return Action.from_delta(delta_x, delta_y)

    def _nearest_adjacent_cell(self, start: Tuple[int, int], target: Tuple[int, int]) -> Tuple[int, int]:
        tx, ty = target
        candidates = [
            (tx - 1, ty - 1),
            (tx, ty - 1),
            (tx + 1, ty - 1),
            (tx - 1, ty),
            (tx + 1, ty),
            (tx - 1, ty + 1),
            (tx, ty + 1),
            (tx + 1, ty + 1),
        ]
        valid_candidates = [candidate for candidate in candidates if self._is_valid(candidate)]
        if not valid_candidates:
            return start
        return min(valid_candidates, key=lambda cell: self._distance_squared(start, cell))

    def _is_valid(self, cell: Tuple[int, int]) -> bool:
        x_pos, y_pos = cell
        if x_pos < 0 or y_pos < 0:
            return False
        if x_pos >= FIELD_DIMENSIONS.width or y_pos >= FIELD_DIMENSIONS.height:
            return False
        return True

    def _distance_squared(self, start: Tuple[int, int], end: Tuple[int, int]) -> float:
        dx = start[0] - end[0]
        dy = start[1] - end[1]
        return float(dx * dx + dy * dy)

    def _nearest_resource(
        self, position: Tuple[int, int], resources: Tuple[Tuple[int, int], ...]
    ) -> Tuple[int, int]:
        if not resources:
            return position
        return min(resources, key=lambda resource: self._distance_squared(position, resource))

