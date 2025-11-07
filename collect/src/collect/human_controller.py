"""Keyboard controller handling for Collect."""

from __future__ import annotations

import pygame

from .types import Action


class HumanController:
    """Maps key presses to actions."""

    _KEY_BINDINGS = {
        pygame.K_q: Action.MOVE_UP_LEFT,
        pygame.K_w: Action.MOVE_UP,
        pygame.K_e: Action.MOVE_UP_RIGHT,
        pygame.K_a: Action.MOVE_LEFT,
        pygame.K_d: Action.MOVE_RIGHT,
        pygame.K_z: Action.MOVE_DOWN_LEFT,
        pygame.K_x: Action.MOVE_DOWN,
        pygame.K_c: Action.MOVE_DOWN_RIGHT,
    }

    def select_action(self, pressed: pygame.key.ScancodeWrapper) -> Action:
        for key, action in self._KEY_BINDINGS.items():
            if pressed[key]:
                return action
        return Action.STAY

