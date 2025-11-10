"""Tests for the CollectPufferAgent."""

from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from typing import Dict

from collect.puffer_agent import CollectPufferAgent
from collect.types import Observation


def test_collect_puffer_agent_act_and_learn() -> None:
    state_size = Observation.vector_length()
    agent = CollectPufferAgent(state_size=state_size, action_size=9)
    state = np.zeros(state_size, dtype=np.float32)
    action = agent.act(state)
    assert isinstance(action, int)
    agent.learn(1.0, state, False)


def test_collect_puffer_agent_validates_state_size() -> None:
    agent = CollectPufferAgent(state_size=Observation.vector_length(), action_size=9)
    with pytest.raises(ValueError):
        agent.act(np.zeros((2, 7), dtype=np.float32))


def test_collect_puffer_agent_uses_three_hidden_layers() -> None:
    agent = CollectPufferAgent(state_size=Observation.vector_length(), action_size=9, hidden_size=64)
    policy = agent._policy
    linear_layers = [module for module in policy._encoder if isinstance(module, torch.nn.Linear)]
    assert len(linear_layers) == 3
    assert all(layer.out_features == 64 for layer in linear_layers)
    assert all(layer.in_features == 64 for layer in linear_layers[1:])


def test_collect_puffer_agent_bootstraps_value_with_next_state() -> None:
    state_size = Observation.vector_length()
    discount = 0.75
    agent = CollectPufferAgent(state_size=state_size, action_size=9, discount=discount)
    agent._max_grad_norm = 1e9  # ensure gradients are not clipped during the test

    state = np.zeros(state_size, dtype=np.float32)
    state[0] = 0.5
    next_state = np.linspace(-1.0, 1.0, state_size, dtype=np.float32)

    agent.act(state)

    value_bias = agent._policy._value_head.bias
    captured_grad: Dict[str, torch.Tensor] = {}

    def _capture_grad(grad: torch.Tensor) -> None:
        captured_grad["bias"] = grad.detach().clone()

    hook = value_bias.register_hook(_capture_grad)
    try:
        state_tensor = torch.from_numpy(agent._to_state_array(state)).to(agent._device)
        next_state_tensor = torch.from_numpy(agent._to_state_array(next_state)).to(agent._device)

        with torch.no_grad():
            _, value = agent._policy.forward_eval(state_tensor.unsqueeze(0))
            _, next_value = agent._policy.forward_eval(next_state_tensor.unsqueeze(0))

        # Ensure next_value has meaningful magnitude so the assertion is robust
        assert not torch.allclose(next_value, torch.zeros_like(next_value)), "next_value should influence the target"

        reward = 1.0
        expected_target = reward + discount * next_value.squeeze(0)

        agent.learn(reward=reward, next_state=next_state, done=False)
    finally:
        hook.remove()

    assert "bias" in captured_grad
    grad = captured_grad["bias"].squeeze()

    value_scalar = value.squeeze(0)
    expected_grad = agent._value_coef * (value_scalar - expected_target)
    torch.testing.assert_close(grad, expected_grad, atol=1e-5, rtol=1e-5)


def test_collect_puffer_agent_terminal_transition_disables_bootstrap() -> None:
    state_size = Observation.vector_length()
    agent = CollectPufferAgent(state_size=state_size, action_size=9, discount=0.9)
    agent._max_grad_norm = 1e9

    state = np.zeros(state_size, dtype=np.float32)
    state[0] = 0.25
    next_state = np.linspace(0.1, 0.9, state_size, dtype=np.float32)

    agent.act(state)

    value_bias = agent._policy._value_head.bias
    captured_grad: Dict[str, torch.Tensor] = {}

    def _capture_grad(grad: torch.Tensor) -> None:
        captured_grad["bias"] = grad.detach().clone()

    hook = value_bias.register_hook(_capture_grad)
    try:
        state_tensor = torch.from_numpy(agent._to_state_array(state)).to(agent._device)

        with torch.no_grad():
            _, value = agent._policy.forward_eval(state_tensor.unsqueeze(0))

        reward = 2.0

        agent.learn(reward=reward, next_state=next_state, done=True)
    finally:
        hook.remove()

    assert "bias" in captured_grad
    grad = captured_grad["bias"].squeeze()

    value_scalar = value.squeeze(0)
    expected_grad = agent._value_coef * (value_scalar - torch.tensor(reward, device=value_scalar.device))
    torch.testing.assert_close(grad, expected_grad, atol=1e-5, rtol=1e-5)