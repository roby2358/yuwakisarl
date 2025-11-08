"""Tests for AIController defaults."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("numpy")

from collect.ai_controller import AIController
from collect.neural_agent import NeuralPolicyAgent


def test_default_agent_prints_neural_when_puffer_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("collect.ai_controller.CollectPufferAgent", None, raising=False)

    agent = AIController.default_agent()
    captured = capsys.readouterr()

    assert isinstance(agent, NeuralPolicyAgent)
    assert "using built-in neural agent" in captured.out


def test_default_agent_prints_pufferlib_when_available(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class DummyAgent:
        def __init__(self) -> None:
            self.initialised = True

        def act(self, *_: Any, **__: Any) -> int:
            return 0

    monkeypatch.setattr("collect.ai_controller.CollectPufferAgent", DummyAgent, raising=False)

    agent = AIController.default_agent()
    captured = capsys.readouterr()

    assert isinstance(agent, DummyAgent)
    assert "using PufferLib agent" in captured.out


def test_controllers_use_distinct_agents() -> None:
    controller_one = AIController(1)
    controller_two = AIController(2)

    assert controller_one._agent is not controller_two._agent
