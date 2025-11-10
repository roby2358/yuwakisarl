import numpy as np

from collect.neural_agent import NeuralPolicyAgent
from collect.types import Observation


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


def test_neural_policy_agent_act_and_learn_updates_all_layers():
    state_size = Observation.vector_length()
    agent = NeuralPolicyAgent(state_size=state_size, action_size=9)
    agent.epsilon = 0.0

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

    agent.learn(reward=1.0, next_state=state)

    assert all(np.any(after != before) for before, after in zip(weights_before, agent._weights))
    assert all(np.any(after != before) for before, after in zip(biases_before, agent._biases))

