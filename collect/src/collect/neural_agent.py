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
    """Simple policy-gradient agent with a single hidden layer."""

    state_size: int
    action_size: int
    hidden_size: int = 64
    learning_rate: float = 0.01
    epsilon: float = 0.8
    epsilon_decay: float = 0.99995
    epsilon_min: float = 0.05
    baseline_momentum: float = 0.99

    _w1: np.ndarray = field(init=False)
    _b1: np.ndarray = field(init=False)
    _w2: np.ndarray = field(init=False)
    _b2: np.ndarray = field(init=False)
    _baseline: float = field(default=0.0, init=False)
    _traces: Dict[int, Tuple[np.ndarray, np.ndarray, np.ndarray, int]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        rng = np.random.default_rng()
        scale1 = math.sqrt(2.0 / max(1, self.state_size))
        scale2 = math.sqrt(2.0 / max(1, self.hidden_size))
        self._w1 = rng.normal(0.0, scale1, size=(self.state_size, self.hidden_size)).astype(np.float32)
        self._b1 = np.zeros(self.hidden_size, dtype=np.float32)
        self._w2 = rng.normal(0.0, scale2, size=(self.hidden_size, self.action_size)).astype(np.float32)
        self._b2 = np.zeros(self.action_size, dtype=np.float32)

    def act(self, state: Sequence[float], actor_id: int = 0) -> int:
        state_vector = np.asarray(state, dtype=np.float32)
        hidden = np.tanh(state_vector @ self._w1 + self._b1)
        logits = hidden @ self._w2 + self._b2
        probs = _softmax(logits)

        if random.random() < self.epsilon:
            action = random.randrange(self.action_size)
        else:
            action = int(np.random.choice(self.action_size, p=probs))

        self._traces[actor_id] = (state_vector, hidden, probs, action)

        self._decay_epsilon()
        return action

    def learn(self, reward: float, next_state: Sequence[float], actor_id: int = 0) -> None:  # noqa: ARG002
        trace = self._traces.pop(actor_id, None)
        if trace is None:
            return

        state, hidden, probs, action = trace

        advantage = reward - self._baseline
        self._baseline = self.baseline_momentum * self._baseline + (1 - self.baseline_momentum) * reward

        one_hot = np.zeros_like(probs)
        one_hot[action] = 1.0

        delta2 = (one_hot - probs) * advantage
        self._w2 += self.learning_rate * np.outer(hidden, delta2)
        self._b2 += self.learning_rate * delta2

        grad_hidden = (delta2 @ self._w2.T) * (1.0 - hidden ** 2)
        self._w1 += self.learning_rate * np.outer(state, grad_hidden)
        self._b1 += self.learning_rate * grad_hidden

    def _decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


