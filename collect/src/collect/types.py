"""Shared types for Collect game."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Tuple


class ControllerType(Enum):
    """Defines how a player selects actions."""

    AI = auto()
    HUMAN = auto()


class Action(Enum):
    """Permitted player actions per tick."""

    STAY = (0, 0)
    MOVE_UP = (0, -1)
    MOVE_DOWN = (0, 1)
    MOVE_LEFT = (-1, 0)
    MOVE_RIGHT = (1, 0)
    MOVE_UP_LEFT = (-1, -1)
    MOVE_UP_RIGHT = (1, -1)
    MOVE_DOWN_LEFT = (-1, 1)
    MOVE_DOWN_RIGHT = (1, 1)

    def delta(self) -> Tuple[int, int]:
        return self.value

    @staticmethod
    def from_delta(delta_x: int, delta_y: int) -> "Action":
        clamped_x = max(-1, min(1, delta_x))
        clamped_y = max(-1, min(1, delta_y))
        mapping: Dict[Tuple[int, int], Action] = {
            action.value: action
            for action in Action
        }
        return mapping[(clamped_x, clamped_y)]


GridPosition = Tuple[int, int]


@dataclass
class Player:
    """Represents a player in the game."""

    identifier: int
    position: GridPosition
    controller: ControllerType
    has_resource: bool = False
    score: int = 0

    def with_position(self, position: GridPosition) -> "Player":
        if position == self.position:
            return self
        return Player(
            identifier=self.identifier,
            position=position,
            controller=self.controller,
            has_resource=self.has_resource,
            score=self.score,
        )

    def with_resource(self, has_resource: bool) -> "Player":
        if has_resource == self.has_resource:
            return self
        return Player(
            identifier=self.identifier,
            position=self.position,
            controller=self.controller,
            has_resource=has_resource,
            score=self.score,
        )

    def with_score(self, score: int) -> "Player":
        if score == self.score:
            return self
        return Player(
            identifier=self.identifier,
            position=self.position,
            controller=self.controller,
            has_resource=self.has_resource,
            score=score,
        )


@dataclass(frozen=True)
class Observation:
    """Snapshot provided to controllers when selecting actions."""

    player: Player
    players: Tuple[Player, ...]
    resources: Tuple[GridPosition, ...]
    target: GridPosition
    monster: GridPosition

