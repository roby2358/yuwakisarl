"""Shared types for Collect game."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple


class ControllerType(Enum):
    """Defines how a player selects actions."""

    AI = auto()
    HUMAN = auto()


class Action(Enum):
    """Permitted player actions per tick."""

    STAY = auto()
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()


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

