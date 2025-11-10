"""Tests for AIController defaults."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("numpy")

from collect.ai_controller import AIController
from collect.neural_agent import NeuralPolicyAgent
from collect.types import ControllerType, Observation, Player


def test_default_agent_uses_neural_when_flag_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyAgent:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr("collect.ai_controller.CollectPufferAgent", DummyAgent, raising=False)
    monkeypatch.delenv("COLLECT_USE_PUFFER", raising=False)

    agent = AIController.default_agent()

    assert isinstance(agent, NeuralPolicyAgent)


def test_default_agent_uses_puffer_when_enabled(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class DummyAgent:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

        def act(self, *_: Any, **__: Any) -> int:
            return 0

    monkeypatch.setattr("collect.ai_controller.CollectPufferAgent", DummyAgent, raising=False)
    monkeypatch.setenv("COLLECT_USE_PUFFER", "true")

    agent = AIController.default_agent()
    captured = capsys.readouterr()

    assert isinstance(agent, DummyAgent)
    assert "using PufferLib agent" in captured.out


def test_default_agent_falls_back_when_puffer_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("collect.ai_controller.CollectPufferAgent", None, raising=False)
    monkeypatch.setenv("COLLECT_USE_PUFFER", "1")

    agent = AIController.default_agent()
    captured = capsys.readouterr()

    assert isinstance(agent, NeuralPolicyAgent)
    assert "falling back to built-in neural agent" in captured.out


def test_controllers_use_distinct_agents() -> None:
    controller_one = AIController(1)
    controller_two = AIController(2)

    assert controller_one._agent is not controller_two._agent


def test_ai_controller_observe_forwards_terminal_flag() -> None:
    controller = AIController(3)

    class DummyAgent:
        def __init__(self) -> None:
            self.calls: list[tuple[float, tuple[float, ...], bool, int]] = []

        def learn(self, reward: float, next_state: tuple[float, ...], done: bool, actor_id: int) -> None:
            self.calls.append((reward, tuple(next_state), done, actor_id))

    dummy_agent = DummyAgent()
    controller._agent = dummy_agent

    player = Player(identifier=3, position=(1, 1), controller=ControllerType.AI)
    observation = Observation(
        player=player,
        players=(player,),
        resources=(),
        monster=(2, 2),
        target=(3, 3),
    )

    controller.observe(1.5, observation, True)
    controller.observe(0.25, observation, False)

    assert dummy_agent.calls == [
        (1.5, observation.as_vector(), True, 3),
        (0.25, observation.as_vector(), False, 3),
    ]
