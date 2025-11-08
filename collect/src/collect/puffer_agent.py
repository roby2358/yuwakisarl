"""PufferLib-based reinforcement learning agent for Collect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence

import numpy as np

try:
    import gymnasium as gym
    import torch
    from torch.distributions import Categorical

    import pufferlib.models
except Exception as exc:  # pragma: no cover - optional dependency bootstrap
    raise ImportError("CollectPufferAgent requires torch, gymnasium, and pufferlib") from exc


_FLOAT_DTYPE = np.float32


@dataclass
class _Trace:
    """Stores transition data for a single actor."""

    state: torch.Tensor
    action: int


class _CollectEnvSpec:
    """Minimal environment spec compatible with pufferlib models."""

    def __init__(self, state_size: int, action_size: int) -> None:
        low = np.full(state_size, -np.inf, dtype=_FLOAT_DTYPE)
        high = np.full(state_size, np.inf, dtype=_FLOAT_DTYPE)
        self.single_observation_space = gym.spaces.Box(low=low, high=high, dtype=_FLOAT_DTYPE)
        self.single_action_space = gym.spaces.Discrete(action_size)
        self.observation_space = self.single_observation_space
        self.action_space = self.single_action_space


class CollectPufferAgent:
    """Single-agent policy that leverages pufferlib's default model."""

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 128,
        learning_rate: float = 3e-4,
        entropy_coef: float = 1e-3,
        value_coef: float = 0.5,
        max_grad_norm: float = 1.0,
    ) -> None:
        if state_size <= 0:
            raise ValueError("state_size must be positive")
        if action_size <= 0:
            raise ValueError("action_size must be positive")

        self._device = torch.device("cpu")
        self._spec = _CollectEnvSpec(state_size, action_size)
        self._policy = pufferlib.models.Default(self._spec, hidden_size=hidden_size).to(self._device)
        self._policy.train()
        self._optimizer = torch.optim.Adam(self._policy.parameters(), lr=learning_rate)
        self._entropy_coef = float(entropy_coef)
        self._value_coef = float(value_coef)
        self._max_grad_norm = float(max_grad_norm)
        self._traces: Dict[int, _Trace] = {}

    def act(self, state: Sequence[float], actor_id: int = 0) -> int:
        state_array = self._to_state_array(state)
        state_tensor = torch.from_numpy(state_array).to(self._device)
        logits, _ = self._policy.forward_eval(state_tensor.unsqueeze(0))
        logits = logits.squeeze(0)
        distribution = Categorical(logits=logits)
        action_tensor = distribution.sample()
        action = int(action_tensor.item())
        self._traces[actor_id] = _Trace(state=state_tensor.detach(), action=action)
        return action

    def learn(self, reward: float, next_state: Sequence[float], actor_id: int = 0) -> None:  # noqa: ARG002
        trace = self._traces.pop(actor_id, None)
        if trace is None:
            return

        reward_tensor = torch.tensor(float(reward), dtype=torch.float32, device=self._device)
        state_tensor = trace.state.unsqueeze(0)

        logits, value = self._policy(state_tensor)
        logits = logits.squeeze(0)
        value = value.squeeze(0)

        distribution = Categorical(logits=logits)
        log_prob = distribution.log_prob(torch.tensor(trace.action, device=self._device))
        advantage = reward_tensor - value

        policy_loss = -log_prob * advantage.detach()
        value_loss = 0.5 * advantage.pow(2)
        entropy_loss = distribution.entropy()

        loss = policy_loss + self._value_coef * value_loss - self._entropy_coef * entropy_loss

        self._optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self._policy.parameters(), self._max_grad_norm)
        self._optimizer.step()

    def observe(self, reward: float, next_state: Sequence[float], actor_id: int = 0) -> None:
        self.learn(reward, next_state, actor_id)

    def _to_state_array(self, state: Sequence[float]) -> np.ndarray:
        state_array = np.asarray(state, dtype=_FLOAT_DTYPE)
        if state_array.ndim != 1:
            raise ValueError("state must be one-dimensional")
        if state_array.size != self._spec.single_observation_space.shape[0]:
            raise ValueError("state size does not match configured state space")
        return state_array


__all__ = ["CollectPufferAgent"]

