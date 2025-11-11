"""AI controller integration with optional PufferLib agents."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Optional

from .neural_agent import NeuralPolicyAgent
from .types import Action, Observation

try:
    from .puffer_agent import CollectPufferAgent
except ImportError:  # pragma: no cover - optional dependency
    CollectPufferAgent = None  # type: ignore[misc]


@dataclass
class AIController:
    """Selects actions for an AI-controlled player."""

    player_identifier: int
    _agent: object = field(init=False)
    _encoded_state_length: int = Observation.vector_length()

    def __post_init__(self) -> None:
        self._agent = self._build_agent()

    def select_action(self, observation: Observation) -> Action:
        agent_action = self._select_agent_action(observation)
        if agent_action is not None:
            return agent_action
        return Action.STAY

    @classmethod
    def default_agent(cls) -> object:
        prefer_puffer = os.getenv("COLLECT_USE_PUFFER", "").strip().lower() in {"1", "true", "yes"}
        if prefer_puffer:
            agent = cls._build_puffer_agent()
            if agent is not None:
                print("AIController: using PufferLib agent")
                return agent
            print("AIController: falling back to built-in neural agent")
        return NeuralPolicyAgent(state_size=cls._encoded_state_length, action_size=len(Action))

    @classmethod
    def _build_puffer_agent(cls) -> Optional[object]:
        if CollectPufferAgent is None:
            return None
        try:
            agent = CollectPufferAgent(state_size=cls._encoded_state_length, action_size=len(Action))
        except TypeError:
            try:
                agent = CollectPufferAgent()  # type: ignore[call-arg]
            except Exception:
                return None
        except Exception:  # pragma: no cover - defensive
            return None
        return agent

    def _build_agent(self) -> object:
        return self.default_agent()

    def _select_agent_action(self, observation: Observation) -> Optional[Action]:
        agent = self._agent
        if agent is None:
            return None
        state_vector = observation.as_vector()
        try:
            raw_action = agent.act(state_vector, self.player_identifier)  # type: ignore[attr-defined]
        except TypeError:
            raw_action = agent.act(state_vector)  # type: ignore[attr-defined]
        return self._map_agent_action(raw_action)

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

    def observe(self, reward: float, next_observation: Observation, is_terminal: bool) -> None:
        agent = self._agent
        if agent is None:
            return
        next_state = next_observation.as_vector()
        if hasattr(agent, "learn"):
            try:
                agent.learn(reward, next_state, is_terminal, self.player_identifier)  # type: ignore[attr-defined]
            except TypeError:
                agent.learn(reward, next_state, is_terminal)  # type: ignore[attr-defined]
        elif hasattr(agent, "observe"):
            try:
                agent.observe(reward, next_state, is_terminal, self.player_identifier)  # type: ignore[attr-defined]
            except TypeError:
                agent.observe(reward, next_state, is_terminal)  # type: ignore[attr-defined]

    def exploration_rate(self) -> float | None:
        agent = self._agent
        if agent is None:
            return None
        if hasattr(agent, "exploration_rate"):
            try:
                epsilon_value = agent.exploration_rate(self.player_identifier)  # type: ignore[attr-defined]
            except TypeError:
                epsilon_value = agent.exploration_rate()  # type: ignore[attr-defined]
            if isinstance(epsilon_value, (int, float)):
                return float(epsilon_value)
        epsilon = getattr(agent, "epsilon", None)
        if isinstance(epsilon, (int, float)):
            return float(epsilon)
        return None

    def randomize_agent(self) -> None:
        agent = self._agent
        if agent is None:
            return
        randomize = getattr(agent, "randomize_weights", None)
        if callable(randomize):
            randomize()
            return
        reset = getattr(agent, "reset", None)
        if callable(reset):
            reset()

    def randomize_agent_percentile(self, percentile: float) -> None:
        agent = self._agent
        if agent is None:
            return
        randomize = getattr(agent, "randomize_percentile_weights", None)
        if callable(randomize):
            randomize(percentile)
            return
        self.randomize_agent()

