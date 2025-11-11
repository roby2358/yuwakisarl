from __future__ import annotations

from types import SimpleNamespace
import pytest

import collect.game as game_module
from collect.ai_controller import AIController
from collect.game import AgentFeedback, Game
from collect.neural_agent import NeuralPolicyAgent
from collect.types import Action, ControllerType, Observation, Player


class DummyController:
    def __init__(self) -> None:
        self.calls: list[tuple[float, Observation, bool]] = []

    def observe(self, reward: float, next_observation: Observation, is_terminal: bool) -> None:
        self.calls.append((reward, next_observation, is_terminal))


def _observation_for(identifier: int) -> Observation:
    player = Player(identifier=identifier, position=(identifier, identifier), controller=ControllerType.AI)
    return Observation(
        player=player,
        players=(player,),
        resources=(),
        monster=(identifier + 1, identifier + 1),
        target=(identifier + 2, identifier + 2),
    )


def test_game_apply_agent_feedback_forwards_terminal_flag() -> None:
    controller = DummyController()
    terminal_observation = _observation_for(0)
    ongoing_observation = _observation_for(1)

    terminal_feedback = [
        AgentFeedback(controller=controller, reward=1.0, next_observation=terminal_observation),
    ]
    ongoing_feedback = [
        AgentFeedback(controller=controller, reward=0.25, next_observation=ongoing_observation),
    ]

    game = Game.__new__(Game)
    game._human_player_identifier = None

    game._apply_agent_feedback(terminal_feedback, True)
    game._apply_agent_feedback(ongoing_feedback, False)

    assert controller.calls == [
        (1.0, terminal_observation, True),
        (0.25, ongoing_observation, False),
    ]


def test_game_epsilon_by_player_returns_mapping() -> None:
    game = Game.__new__(Game)
    agent_a = NeuralPolicyAgent(
        state_size=Observation.vector_length(),
        action_size=len(Action),
    )
    agent_b = NeuralPolicyAgent(
        state_size=Observation.vector_length(),
        action_size=len(Action),
    )
    agent_a._epsilon_values[0] = 0.4
    agent_b._epsilon_values[1] = 0.2

    controller_a = AIController.__new__(AIController)
    controller_a.player_identifier = 0
    controller_a._agent = agent_a
    controller_b = AIController.__new__(AIController)
    controller_b.player_identifier = 1
    controller_b._agent = agent_b

    game._ai_controllers = {
        0: controller_a,
        1: controller_b,
    }

    epsilon_map = game._epsilon_by_player()

    assert epsilon_map is not None
    assert epsilon_map[0] == pytest.approx(40.0)
    assert epsilon_map[1] == pytest.approx(20.0)


class _StubController:
    def __init__(self) -> None:
        self.randomized = False
        self.called_percentiles: list[float | None] = []

    def randomize_agent(self) -> None:
        self.randomized = True
        self.called_percentiles.append(None)

    def randomize_agent_percentile(self, percentile: float) -> None:
        self.randomized = True
        self.called_percentiles.append(percentile)


class _StubRollingScore:
    def __init__(self, values: dict[int, int] | None = None) -> None:
        self.values = values or {}

    def record(self, player_identifier: int, timestamp: float, count: int = 1) -> None:  # pragma: no cover - stub
        pass

    def total(self, player_identifier: int, current_time: float) -> int:
        return self.values.get(player_identifier, 0)

    def totals(self, current_time: float) -> dict[int, int]:
        return dict(self.values)


def test_game_randomize_lowest_agent_respects_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    players = (
        Player(identifier=0, position=(0, 0), controller=ControllerType.AI, score=5),
        Player(identifier=1, position=(0, 0), controller=ControllerType.AI, score=1),
        Player(identifier=2, position=(0, 0), controller=ControllerType.AI, score=1),
    )
    jitter_values = iter([0.2, 0.8, 0.1])
    monkeypatch.setattr(game_module.random, "random", lambda: next(jitter_values))
    monkeypatch.setattr(game_module.random, "choice", lambda seq: seq[-1])

    game = Game.__new__(Game)
    game._state = SimpleNamespace(players=players)
    game._ai_controllers = {
        0: _StubController(),
        1: _StubController(),
        2: _StubController(),
    }
    game._human_player_identifier = None
    game._next_randomization_time = 0.0
    game._rolling_score = _StubRollingScore({0: 4, 1: 1, 2: 0})

    game._maybe_randomize_lowest_agent(0.0)

    assert game._ai_controllers[2].randomized is True
    assert game._ai_controllers[0].randomized is True
    assert game._ai_controllers[1].randomized is False
    assert len(game._ai_controllers[2].called_percentiles) == 1
    assert game._ai_controllers[2].called_percentiles[0] == pytest.approx(50.0)
    assert len(game._ai_controllers[0].called_percentiles) == 1
    assert game._ai_controllers[0].called_percentiles[0] == pytest.approx(20.0)
    assert game._ai_controllers[1].called_percentiles == []
    assert game._next_randomization_time == pytest.approx(Game._RANDOMIZATION_INTERVAL_SECONDS)


def test_game_randomize_lowest_agent_waits_for_interval() -> None:
    players = (
        Player(identifier=0, position=(0, 0), controller=ControllerType.AI, score=0),
    )
    game = Game.__new__(Game)
    game._state = SimpleNamespace(players=players)
    controller = _StubController()
    game._ai_controllers = {0: controller}
    game._human_player_identifier = None
    game._next_randomization_time = 100.0
    game._rolling_score = _StubRollingScore({0: 2})

    game._maybe_randomize_lowest_agent(50.0)

    assert controller.randomized is False


def test_game_randomize_lowest_agent_single_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    players = (
        Player(identifier=0, position=(0, 0), controller=ControllerType.AI, score=2),
    )
    game = Game.__new__(Game)
    game._state = SimpleNamespace(players=players)
    controller = _StubController()
    game._ai_controllers = {0: controller}
    game._human_player_identifier = None
    game._next_randomization_time = 0.0
    game._rolling_score = _StubRollingScore({0: 0})

    monkeypatch.setattr(game_module.random, "random", lambda: 0.5)

    def choice_fail(seq):  # pragma: no cover - sanity guard
        raise AssertionError("random.choice should not be invoked when only one candidate exists")

    monkeypatch.setattr(game_module.random, "choice", choice_fail)

    game._maybe_randomize_lowest_agent(0.0)

    assert controller.randomized is True
    assert len(controller.called_percentiles) == 1
    assert controller.called_percentiles[0] == pytest.approx(50.0)

