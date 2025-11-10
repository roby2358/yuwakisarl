"""Tests for the CollectPufferAgent."""

from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from collect.puffer_agent import CollectPufferAgent


def test_collect_puffer_agent_act_and_learn() -> None:
    agent = CollectPufferAgent(state_size=14, action_size=9)
    state = np.zeros(14, dtype=np.float32)
    action = agent.act(state)
    assert isinstance(action, int)
    agent.learn(1.0, state)


def test_collect_puffer_agent_validates_state_size() -> None:
    agent = CollectPufferAgent(state_size=14, action_size=9)
    with pytest.raises(ValueError):
        agent.act(np.zeros((2, 7), dtype=np.float32))


def test_collect_puffer_agent_uses_three_hidden_layers() -> None:
    agent = CollectPufferAgent(state_size=14, action_size=9, hidden_size=64)
    policy = agent._policy
    linear_layers = [module for module in policy._encoder if isinstance(module, torch.nn.Linear)]
    assert len(linear_layers) == 3
    assert all(layer.out_features == 64 for layer in linear_layers)
    assert all(layer.in_features == 64 for layer in linear_layers[1:])