"""AI controller integration with optional PufferLib agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from .config import FIELD_DIMENSIONS
from .neural_agent import NeuralPolicyAgent
from .types import Action, Observation, Player

try:
    from .puffer_agent import CollectPufferAgent
except ImportError:  # pragma: no cover - optional dependency
    CollectPufferAgent = None  # type: ignore[misc]


@dataclass
class AIController:
    """Selects actions for an AI-controlled player."""

    player_identifier: int
    shared_agent: Optional[object] = None
    _encoded_state_length: int = 14

    def __post_init__(self) -> None:
        self._agent = self.shared_agent if self.shared_agent is not None else self._build_agent()

    def select_action(self, observation: Observation) -> Action:
        agent_action = self._select_agent_action(observation)
        if agent_action is not None:
            return agent_action
        return Action.STAY

    @classmethod
    def default_agent(cls) -> object:
        agent = cls._build_puffer_agent()
        if agent is not None:
            return agent
        print("AIController: using built-in neural agent")
        return NeuralPolicyAgent(state_size=cls._encoded_state_length, action_size=len(Action))

    @classmethod
    def _build_puffer_agent(cls) -> Optional[object]:
        if CollectPufferAgent is None:
            return None
        try:
            agent = CollectPufferAgent(state_size=cls._encoded_state_length, action_size=len(Action))
        except Exception:  # pragma: no cover - defensive
            return None
        print("AIController: using PufferLib agent")
        return agent

    def _build_agent(self) -> object:
        return self.default_agent()

    def _select_agent_action(self, observation: Observation) -> Optional[Action]:
        agent = self._agent
        if agent is None:
            return None
        state_vector = self._encode_observation(observation)
        try:
            raw_action = agent.act(state_vector, self.player_identifier)  # type: ignore[attr-defined]
        except TypeError:
            raw_action = agent.act(state_vector)  # type: ignore[attr-defined]
        return self._map_agent_action(raw_action)

    def _encode_observation(self, observation: Observation) -> Sequence[float]:
        player = observation.player
        px, py = player.position
        tx, ty = observation.target
        rx, ry = self._nearest_resource(player.position, observation.resources)
        nearest_player_offset = self._nearest_player_offset(player, observation.players)
        width = max(1, FIELD_DIMENSIONS.width - 1)
        height = max(1, FIELD_DIMENSIONS.height - 1)
        px_n = float(px) / width
        py_n = float(py) / height
        rx_n = float(rx) / width
        ry_n = float(ry) / height
        tx_n = float(tx) / width
        ty_n = float(ty) / height
        dx_resource = (rx - px) / width
        dy_resource = (ry - py) / height
        dx_player = nearest_player_offset[0] / width
        dy_player = nearest_player_offset[1] / height
        if player.has_resource:
            dx_target = (tx - px) / width
            dy_target = (ty - py) / height
        else:
            dx_target = dx_resource
            dy_target = dy_resource
        has_resource = 1.0 if player.has_resource else 0.0
        score = float(player.score)
        return (
            px_n,
            py_n,
            rx_n,
            ry_n,
            tx_n,
            ty_n,
            dx_resource,
            dy_resource,
            dx_target,
            dy_target,
            dx_player,
            dy_player,
            has_resource,
            score,
        )

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

    def _nearest_player_offset(self, player: Player, players: Tuple[Player, ...]) -> Tuple[int, int]:
        candidates = [other for other in players if other.identifier != player.identifier]
        if not candidates:
            return (0, 0)
        closest = min(candidates, key=lambda other: self._distance_squared(player.position, other.position))
        return (closest.position[0] - player.position[0], closest.position[1] - player.position[1])

    def observe(self, reward: float, next_observation: Observation) -> None:
        agent = self._agent
        if agent is None:
            return
        next_state = self._encode_observation(next_observation)
        if hasattr(agent, "learn"):
            try:
                agent.learn(reward, next_state, self.player_identifier)  # type: ignore[attr-defined]
            except TypeError:
                agent.learn(reward, next_state)  # type: ignore[attr-defined]
        elif hasattr(agent, "observe"):
            try:
                agent.observe(reward, next_state, self.player_identifier)  # type: ignore[attr-defined]
            except TypeError:
                agent.observe(reward, next_state)  # type: ignore[attr-defined]

