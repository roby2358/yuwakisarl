"""Keyboard controller handling for Collect."""

from __future__ import annotations

import pygame

from .types import Action


class HumanController:
    """Maps key presses to actions."""

    _KEY_BINDINGS = {
        pygame.K_a: Action.MOVE_LEFT,
        pygame.K_s: Action.MOVE_DOWN,
        pygame.K_w: Action.MOVE_UP,
        pygame.K_d: Action.MOVE_RIGHT,
    }

    def select_action(self, pressed: pygame.key.ScancodeWrapper) -> Action:
        for key, action in self._KEY_BINDINGS.items():
            if pressed[key]:
                return action
        return Action.STAY

