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
    hidden_size: int = 16
    hidden_layers: int = 2
    learning_rate: float = 0.01
    epsilon_start: float = 0.6
    epsilon_decay: float = 0.99995
    epsilon_min: float = 0.05
    baseline_momentum: float = 0.99

    _weights: Tuple[np.ndarray, ...] = field(init=False)
    _biases: Tuple[np.ndarray, ...] = field(init=False)
    _baseline: float = field(default=0.0, init=False)
    _traces: Dict[int, Tuple[Tuple[np.ndarray, ...], np.ndarray, int]] = field(default_factory=dict, init=False)
    _epsilon_values: Dict[int, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.hidden_layers < 1:
            msg = f"hidden_layers must be >= 1 (got {self.hidden_layers})"
            raise ValueError(msg)

        rng = np.random.default_rng()
        self._weights, self._biases = self._initialize_parameters(rng)

    def act(self, state: Sequence[float], actor_id: int = 0) -> int:
        state_vector = np.asarray(state, dtype=np.float32)

        activations = [state_vector]

        current = state_vector
        for layer_index in range(self.hidden_layers):
            current = np.tanh(current @ self._weights[layer_index] + self._biases[layer_index])
            activations.append(current)

        logits = current @ self._weights[-1] + self._biases[-1]
        probs = _softmax(logits)

        epsilon = self._epsilon_for(actor_id)
        if random.random() < epsilon:
            action = random.randrange(self.action_size)
        else:
            action = int(np.random.choice(self.action_size, p=probs))

        self._traces[actor_id] = (tuple(activations), probs, action)

        self._decay_epsilon(actor_id)
        return action

    def learn(self, reward: float, next_state: Sequence[float], done: bool, actor_id: int = 0) -> None:  # noqa: ARG002
        trace = self._traces.pop(actor_id, None)
        if trace is None:
            return

        activations, probs, action = trace

        advantage = reward - self._baseline
        self._baseline = self.baseline_momentum * self._baseline + (1 - self.baseline_momentum) * reward

        one_hot = np.zeros_like(probs)
        one_hot[action] = 1.0

        delta2 = (one_hot - probs) * advantage
        final_activation = activations[-1]
        if np.allclose(final_activation, 0.0):
            final_activation = np.ones_like(final_activation)
        weight_updates = [np.zeros_like(layer) for layer in self._weights]
        bias_updates = [np.zeros_like(layer) for layer in self._biases]
        weight_updates[-1] = self.learning_rate * np.outer(final_activation, delta2)
        bias_updates[-1] = self.learning_rate * delta2

        delta = delta2
        for layer_index in range(self.hidden_layers - 1, -1, -1):
            hidden_output = activations[layer_index + 1]
            derivative = 1.0 - hidden_output**2
            delta = (delta @ self._weights[layer_index + 1].T) * derivative
            layer_activation = activations[layer_index]
            if np.allclose(layer_activation, 0.0):
                layer_activation = np.ones_like(layer_activation)
            weight_updates[layer_index] = self.learning_rate * np.outer(layer_activation, delta)
            bias_updates[layer_index] = self.learning_rate * delta

        self._weights = tuple(base + update for base, update in zip(self._weights, weight_updates))
        self._biases = tuple(base + update for base, update in zip(self._biases, bias_updates))

    def exploration_rate(self, actor_id: int | None = None) -> float:
        key = 0 if actor_id is None else actor_id
        return self._epsilon_for(key)

    def _epsilon_for(self, actor_id: int) -> float:
        epsilon = self._epsilon_values.get(actor_id)
        if epsilon is None:
            epsilon = self.epsilon_start
            self._epsilon_values[actor_id] = epsilon
        return epsilon

    def _decay_epsilon(self, actor_id: int) -> None:
        current = self._epsilon_for(actor_id)
        self._epsilon_values[actor_id] = max(self.epsilon_min, current * self.epsilon_decay)

    def randomize_weights(self) -> None:
        rng = np.random.default_rng()
        self._weights, self._biases = self._initialize_parameters(rng)
        self._reset_exploration_rates()

    def randomize_percentile_weights(self, percentile: float) -> None:
        if percentile <= 0.0:
            return
        if percentile >= 100.0:
            self.randomize_weights()
            return

        flat_abs = [
            np.abs(layer).ravel()
            for layer in (*self._weights, *self._biases)
        ]
        if not flat_abs:
            return

        combined = np.concatenate(flat_abs)
        if combined.size == 0:
            return

        threshold = float(np.percentile(combined, percentile))
        rng = np.random.default_rng()

        updated_weights = []
        updated_biases = []
        fan_in = self.state_size

        for layer_index in range(self.hidden_layers):
            weight = self._weights[layer_index].copy()
            bias = self._biases[layer_index].copy()
            layer_scale = self._layer_scale(fan_in)

            mask = np.abs(weight) <= threshold
            if np.any(mask):
                weight[mask] = rng.normal(0.0, layer_scale, size=int(np.count_nonzero(mask))).astype(np.float32)

            bias_mask = np.abs(bias) <= threshold
            if np.any(bias_mask):
                bias[bias_mask] = rng.normal(0.0, layer_scale, size=int(np.count_nonzero(bias_mask))).astype(np.float32)

            updated_weights.append(weight.astype(np.float32, copy=False))
            updated_biases.append(bias.astype(np.float32, copy=False))
            fan_in = self.hidden_size

        output_weight = self._weights[-1].copy()
        output_bias = self._biases[-1].copy()
        output_scale = self._layer_scale(fan_in)

        mask = np.abs(output_weight) <= threshold
        if np.any(mask):
            output_weight[mask] = rng.normal(0.0, output_scale, size=int(np.count_nonzero(mask))).astype(np.float32)

        bias_mask = np.abs(output_bias) <= threshold
        if np.any(bias_mask):
            output_bias[bias_mask] = rng.normal(0.0, output_scale, size=int(np.count_nonzero(bias_mask))).astype(np.float32)

        updated_weights.append(output_weight.astype(np.float32, copy=False))
        updated_biases.append(output_bias.astype(np.float32, copy=False))

        self._weights = tuple(updated_weights)
        self._biases = tuple(updated_biases)
        self._reset_exploration_rates()

    def _initialize_parameters(
        self,
        rng: np.random.Generator,
    ) -> tuple[tuple[np.ndarray, ...], tuple[np.ndarray, ...]]:
        weights = []
        biases = []

        fan_in = self.state_size
        for _ in range(self.hidden_layers):
            scale = self._layer_scale(fan_in)
            weight = rng.normal(0.0, scale, size=(fan_in, self.hidden_size)).astype(np.float32)
            bias = rng.normal(0.0, scale, size=self.hidden_size).astype(np.float32)
            weights.append(weight)
            biases.append(bias)
            fan_in = self.hidden_size

        output_scale = self._layer_scale(fan_in)
        output_weight = rng.normal(0.0, output_scale, size=(fan_in, self.action_size)).astype(np.float32)
        output_bias = rng.normal(0.0, output_scale, size=self.action_size).astype(np.float32)

        weights.append(output_weight)
        biases.append(output_bias)

        return tuple(weights), tuple(biases)

    @staticmethod
    def _layer_scale(fan_in: int) -> float:
        if fan_in <= 0:
            return 1.0
        return math.sqrt(2.0 / fan_in)

    def _reset_exploration_rates(self) -> None:
        if not self._epsilon_values:
            return
        self._epsilon_values = {actor_id: self.epsilon_start for actor_id in self._epsilon_values}


