"""PufferLib-based reinforcement learning agent for Collect."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Dict, Sequence

import numpy as np

import gymnasium as gym
import torch
from torch.distributions import Categorical

try:
    import pufferlib.pytorch as _puffer_torch
except Exception as exc:  # pragma: no cover - optional dependency bootstrap
    _puffer_torch = None
    warnings.warn(
        "pufferlib not available; CollectPufferAgent is using an internal initialization shim.",
        ImportWarning,
    )
    def _layer_init(layer: torch.nn.Linear, std: float = float(np.sqrt(2.0)), bias_const: float = 0.0) -> torch.nn.Linear:
        """Fallback CleanRL-style layer initialization."""
        torch.nn.init.orthogonal_(layer.weight, std)
        torch.nn.init.constant_(layer.bias, bias_const)
        return layer
else:  # pragma: no cover - smoke tests rely on shim path
    def _layer_init(layer: torch.nn.Linear, std: float = float(np.sqrt(2.0)), bias_const: float = 0.0) -> torch.nn.Linear:
        return _puffer_torch.layer_init(layer, std=std, bias_const=bias_const)


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


class _DensePolicy(torch.nn.Module):
    """Two-layer MLP policy for Collect."""

    def __init__(self, spec: _CollectEnvSpec, hidden_size: int) -> None:
        super().__init__()
        observation_shape = spec.single_observation_space.shape
        if len(observation_shape) != 1:
            raise ValueError("Collect environment expects flat observations")
        observation_dim = int(np.prod(observation_shape))
        action_dim = int(spec.single_action_space.n)

        self._encoder = torch.nn.Sequential(
            _layer_init(torch.nn.Linear(observation_dim, hidden_size)),
            torch.nn.GELU(),
            _layer_init(torch.nn.Linear(hidden_size, hidden_size)),
            torch.nn.GELU(),
            _layer_init(torch.nn.Linear(hidden_size, hidden_size)),
            torch.nn.GELU(),
        )
        self._policy_head = _layer_init(
            torch.nn.Linear(hidden_size, action_dim),
            std=0.01,
        )
        self._value_head = _layer_init(
            torch.nn.Linear(hidden_size, 1),
            std=1.0,
        )

    def forward_eval(self, observations: torch.Tensor, state: Dict[str, torch.Tensor] | None = None) -> tuple[torch.Tensor, torch.Tensor]:
        encoded = self.encode_observations(observations, state)
        return self.decode_actions(encoded)

    def forward(self, observations: torch.Tensor, state: Dict[str, torch.Tensor] | None = None) -> tuple[torch.Tensor, torch.Tensor]:
        return self.forward_eval(observations, state)

    def encode_observations(self, observations: torch.Tensor, state: Dict[str, torch.Tensor] | None = None) -> torch.Tensor:
        if observations.ndim == 1:
            raise ValueError("Observations must include a batch dimension")
        batch_size = observations.shape[0]
        flattened = observations.view(batch_size, -1)
        return self._encoder(flattened.float())

    def decode_actions(self, hidden: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        logits = self._policy_head(hidden)
        values = self._value_head(hidden)
        return logits, values


class CollectPufferAgent:
    """Single-agent policy powered by a widened two-layer MLP."""

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 640,
        learning_rate: float = 3e-4,
        entropy_coef: float = 1e-3,
        value_coef: float = 0.5,
        max_grad_norm: float = 1.0,
        discount: float = 0.99,
    ) -> None:
        if state_size <= 0:
            raise ValueError("state_size must be positive")
        if action_size <= 0:
            raise ValueError("action_size must be positive")
        if discount < 0.0 or discount > 1.0:
            raise ValueError("discount must be between 0.0 and 1.0")

        self._device = torch.device("cpu")
        self._spec = _CollectEnvSpec(state_size, action_size)
        self._policy = _DensePolicy(self._spec, hidden_size=hidden_size).to(self._device)
        self._policy.train()
        self._optimizer = torch.optim.Adam(self._policy.parameters(), lr=learning_rate)
        self._entropy_coef = float(entropy_coef)
        self._value_coef = float(value_coef)
        self._max_grad_norm = float(max_grad_norm)
        self._discount = float(discount)
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

    def learn(self, reward: float, next_state: Sequence[float], done: bool, actor_id: int = 0) -> None:
        trace = self._traces.pop(actor_id, None)
        if trace is None:
            return

        reward_tensor = torch.tensor(float(reward), dtype=torch.float32, device=self._device)
        state_tensor = trace.state.unsqueeze(0)

        logits, value = self._policy(state_tensor)
        logits = logits.squeeze(0)
        value = value.squeeze(0)

        if done:
            target_value = reward_tensor
        else:
            next_state_array = self._to_state_array(next_state)
            next_state_tensor = torch.from_numpy(next_state_array).to(self._device)
            with torch.no_grad():
                _, next_value = self._policy.forward_eval(next_state_tensor.unsqueeze(0))
            next_value = next_value.squeeze(0)
            target_value = reward_tensor + self._discount * next_value

        advantage = target_value - value

        distribution = Categorical(logits=logits)
        log_prob = distribution.log_prob(torch.tensor(trace.action, device=self._device))

        policy_loss = -log_prob * advantage.detach()
        value_loss = 0.5 * advantage.pow(2)
        entropy_loss = distribution.entropy()

        loss = policy_loss + self._value_coef * value_loss - self._entropy_coef * entropy_loss

        self._optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self._policy.parameters(), self._max_grad_norm)
        self._optimizer.step()

    def observe(self, reward: float, next_state: Sequence[float], done: bool, actor_id: int = 0) -> None:
        self.learn(reward, next_state, done, actor_id)

    def _to_state_array(self, state: Sequence[float]) -> np.ndarray:
        state_array = np.asarray(state, dtype=_FLOAT_DTYPE)
        if state_array.ndim != 1:
            raise ValueError("state must be one-dimensional")
        if state_array.size != self._spec.single_observation_space.shape[0]:
            raise ValueError("state size does not match configured state space")
        return state_array


__all__ = ["CollectPufferAgent"]

