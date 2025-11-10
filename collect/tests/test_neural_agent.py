from __future__ import annotations

import numpy as np
import pytest

from collect.neural_agent import NeuralPolicyAgent
from collect.types import Observation


def test_neural_policy_agent_uses_configured_architecture() -> None:
    agent = NeuralPolicyAgent(state_size=9, action_size=9)

    assert agent.hidden_size == 128
    assert agent.hidden_layers == 2

    weights = agent._weights  # pylint: disable=protected-access
    biases = agent._biases  # pylint: disable=protected-access

    assert len(weights) == agent.hidden_layers + 1 == 3
    assert weights[0].shape == (9, 128)
    assert weights[1].shape == (128, 128)
    assert weights[2].shape == (128, 9)

    assert len(biases) == agent.hidden_layers + 1 == 3
    assert biases[0].shape == (128,)
    assert biases[1].shape == (128,)
    assert biases[-1].shape == (9,)

    sample_state = np.zeros(9, dtype=np.float32)
    action = agent.act(sample_state, actor_id=0)

    assert 0 <= action < 9


def test_neural_policy_agent_initializes_multi_layer():
    state_size = Observation.vector_length()
    agent = NeuralPolicyAgent(state_size=state_size, action_size=9)

    assert len(agent._weights) == agent.hidden_layers + 1
    assert len(agent._biases) == agent.hidden_layers + 1
    assert agent._weights[0].shape == (agent.state_size, agent.hidden_size)
    assert agent._biases[0].shape == (agent.hidden_size,)

    for layer_index in range(1, agent.hidden_layers):
        assert agent._weights[layer_index].shape == (agent.hidden_size, agent.hidden_size)
        assert agent._biases[layer_index].shape == (agent.hidden_size,)

    assert agent._weights[-1].shape == (agent.hidden_size, agent.action_size)
    assert agent._biases[-1].shape == (agent.action_size,)
    assert agent.exploration_rate() == pytest.approx(0.6)


def test_neural_policy_agent_act_and_learn_updates_all_layers():
    state_size = Observation.vector_length()
    agent = NeuralPolicyAgent(state_size=state_size, action_size=9)
    agent._epsilon_values[0] = 0.0
    agent.epsilon_min = 0.0

    state = np.zeros(agent.state_size, dtype=np.float32)
    action = agent.act(state)

    assert 0 <= action < agent.action_size
    assert 0 in agent._traces

    activations, probs, stored_action = agent._traces[0]
    assert len(activations) == agent.hidden_layers + 1
    assert probs.shape == (agent.action_size,)
    assert stored_action == action

    weights_before = tuple(weight.copy() for weight in agent._weights)
    biases_before = tuple(bias.copy() for bias in agent._biases)

    agent.learn(reward=1.0, next_state=state, done=False)

    assert all(np.any(after != before) for before, after in zip(weights_before, agent._weights))
    assert all(np.any(after != before) for before, after in zip(biases_before, agent._biases))


def test_neural_policy_agent_backprop_uses_pre_update_weights():
    state_size = Observation.vector_length()
    agent = NeuralPolicyAgent(
        state_size=state_size,
        action_size=3,
        hidden_size=2,
        hidden_layers=1,
        learning_rate=0.5,
    )
    agent.baseline_momentum = 0.5

    state = np.zeros(state_size, dtype=np.float32)
    state[0] = 0.25
    state[1] = -0.4

    weight_hidden = np.zeros((state_size, agent.hidden_size), dtype=np.float32)
    weight_hidden[0] = [0.5, -0.3]
    weight_hidden[1] = [-0.4, 0.2]
    bias_hidden = np.array([0.1, -0.2], dtype=np.float32)

    weight_output = np.array(
        [
            [0.2, -0.1, 0.05],
            [0.3, 0.4, -0.2],
        ],
        dtype=np.float32,
    )
    bias_output = np.array([0.0, 0.05, -0.15], dtype=np.float32)

    agent._weights = (weight_hidden.copy(), weight_output.copy())
    agent._biases = (bias_hidden.copy(), bias_output.copy())

    hidden_pre = state @ weight_hidden + bias_hidden
    hidden = np.tanh(hidden_pre)

    logits = hidden @ weight_output + bias_output
    shifted = logits - np.max(logits)
    probs = np.exp(shifted)
    probs /= np.sum(probs)

    action = 1
    agent._traces[0] = ((state, hidden), probs, action)

    reward = 1.5
    initial_baseline = 0.3
    agent._baseline = initial_baseline

    expected_weights = [layer.copy() for layer in agent._weights]
    expected_biases = [layer.copy() for layer in agent._biases]

    advantage = reward - initial_baseline
    delta2 = (np.eye(probs.size)[action] - probs) * advantage
    expected_weights[-1] += agent.learning_rate * np.outer(hidden, delta2)
    expected_biases[-1] += agent.learning_rate * delta2

    derivative = 1.0 - hidden**2
    delta_hidden = (delta2 @ agent._weights[1].T) * derivative
    expected_weights[0] += agent.learning_rate * np.outer(state, delta_hidden)
    expected_biases[0] += agent.learning_rate * delta_hidden

    expected_baseline = agent.baseline_momentum * initial_baseline + (1 - agent.baseline_momentum) * reward

    agent.learn(reward=reward, next_state=state, done=False)

    np.testing.assert_allclose(agent._weights[0], expected_weights[0], rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(agent._weights[1], expected_weights[1], rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(agent._biases[0], expected_biases[0], rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(agent._biases[1], expected_biases[1], rtol=1e-6, atol=1e-6)
    assert agent._baseline == pytest.approx(expected_baseline)


def test_neural_policy_agent_epsilon_decay_progresses_monotonically():
    state_size = Observation.vector_length()
    agent = NeuralPolicyAgent(state_size=state_size, action_size=9)
    agent._epsilon_values[0] = 1.0
    agent.epsilon_min = 0.0

    agent._decay_epsilon(0)

    assert agent.exploration_rate() == pytest.approx(agent.epsilon_decay)


def test_neural_policy_agent_tracks_epsilon_per_actor_independently():
    state_size = Observation.vector_length()
    agent = NeuralPolicyAgent(state_size=state_size, action_size=9, epsilon_start=0.5, epsilon_min=0.0)
    agent._epsilon_values[1] = 1.0
    agent._epsilon_values[2] = 0.25

    agent._decay_epsilon(1)

    assert agent.exploration_rate(1) == pytest.approx(max(agent.epsilon_min, 1.0 * agent.epsilon_decay))
    assert agent.exploration_rate(2) == pytest.approx(0.25)