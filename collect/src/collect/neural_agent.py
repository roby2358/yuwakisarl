"""Lightweight neural-network policy agent for Collect."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Sequence, Tuple

import numpy as np


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    return exp / np.sum(exp)


@dataclass
class NeuralPolicyAgent:
    """Simple policy-gradient agent with multiple hidden layers."""

    state_size: int
    action_size: int
    hidden_size: int = 128
    hidden_layers: int = 3
    learning_rate: float = 0.01
    epsilon: float = 0.8
    epsilon_decay: float = 0.99995
    epsilon_min: float = 0.05
    baseline_momentum: float = 0.99

    _weights: Tuple[np.ndarray, ...] = field(init=False)
    _biases: Tuple[np.ndarray, ...] = field(init=False)
    _baseline: float = field(default=0.0, init=False)
    _traces: Dict[int, Tuple[Tuple[np.ndarray, ...], np.ndarray, int]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.hidden_layers < 1:
            msg = f"hidden_layers must be >= 1 (got {self.hidden_layers})"
            raise ValueError(msg)

        rng = np.random.default_rng()
        weights = []
        biases = []

        fan_in = self.state_size
        for _ in range(self.hidden_layers):
            layer_scale = math.sqrt(2.0 / max(1, fan_in))
            weight = rng.normal(0.0, layer_scale, size=(fan_in, self.hidden_size)).astype(np.float32)
            bias = np.zeros(self.hidden_size, dtype=np.float32)
            weights.append(weight)
            biases.append(bias)
            fan_in = self.hidden_size

        output_scale = math.sqrt(2.0 / max(1, fan_in))
        output_weight = rng.normal(0.0, output_scale, size=(fan_in, self.action_size)).astype(np.float32)
        output_bias = np.zeros(self.action_size, dtype=np.float32)

        weights.append(output_weight)
        biases.append(output_bias)

        self._weights = tuple(weights)
        self._biases = tuple(biases)

    def act(self, state: Sequence[float], actor_id: int = 0) -> int:
        state_vector = np.asarray(state, dtype=np.float32)

        activations = [state_vector]
        current = state_vector
        for layer_index in range(self.hidden_layers):
            current = np.tanh(current @ self._weights[layer_index] + self._biases[layer_index])
            activations.append(current)

        logits = activations[-1] @ self._weights[-1] + self._biases[-1]
        probs = _softmax(logits)

        if random.random() < self.epsilon:
            action = random.randrange(self.action_size)
        else:
            action = int(np.random.choice(self.action_size, p=probs))

        self._traces[actor_id] = (tuple(activations), probs, action)

        self._decay_epsilon()
        return action

    def learn(self, reward: float, next_state: Sequence[float], actor_id: int = 0) -> None:  # noqa: ARG002
        trace = self._traces.pop(actor_id, None)
        if trace is None:
            return

        activations, probs, action = trace

        advantage = reward - self._baseline
        self._baseline = self.baseline_momentum * self._baseline + (1 - self.baseline_momentum) * reward

        one_hot = np.zeros_like(probs)
        one_hot[action] = 1.0

        delta2 = (one_hot - probs) * advantage
        self._weights[-1] += self.learning_rate * np.outer(activations[-1], delta2)
        self._biases[-1] += self.learning_rate * delta2

        delta = delta2
        for layer_index in range(self.hidden_layers - 1, -1, -1):
            hidden_output = activations[layer_index + 1]
            derivative = 1.0 - hidden_output**2
            delta = (delta @ self._weights[layer_index + 1].T) * derivative
            self._weights[layer_index] += self.learning_rate * np.outer(activations[layer_index], delta)
            self._biases[layer_index] += self.learning_rate * delta

    def _decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


