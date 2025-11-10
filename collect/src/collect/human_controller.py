"""Keyboard controller handling for Collect."""

from __future__ import annotations

from typing import Dict

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
    pygame = None  # type: ignore[assignment]

from .types import Action


if pygame is not None:
    _DEFAULT_KEY_BINDINGS: Dict[int, Action] = {
        pygame.K_q: Action.MOVE_UP_LEFT,
        pygame.K_w: Action.MOVE_UP,
        pygame.K_e: Action.MOVE_UP_RIGHT,
        pygame.K_a: Action.MOVE_LEFT,
        pygame.K_d: Action.MOVE_RIGHT,
        pygame.K_z: Action.MOVE_DOWN_LEFT,
        pygame.K_x: Action.MOVE_DOWN,
        pygame.K_c: Action.MOVE_DOWN_RIGHT,
    }
else:  # pragma: no cover - exercised only when pygame missing
    _DEFAULT_KEY_BINDINGS = {}


class HumanController:
    """Maps key presses to actions."""

    _KEY_BINDINGS: Dict[int, Action] = _DEFAULT_KEY_BINDINGS

    def select_action(self, pressed: "pygame.key.ScancodeWrapper") -> Action:  # type: ignore[name-defined]
        if pygame is None:
            raise RuntimeError("pygame is required for HumanController inputs; install pygame to use keyboard control")
        for key, action in self._KEY_BINDINGS.items():
            if pressed[key]:
                return action
        return Action.STAY

