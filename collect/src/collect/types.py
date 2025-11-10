"""Shared types for Collect game."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Iterable, Optional, Tuple

from .config import FIELD_DIMENSIONS


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


def _distance_squared(a: GridPosition, b: GridPosition) -> int:
    delta_x = a[0] - b[0]
    delta_y = a[1] - b[1]
    return delta_x * delta_x + delta_y * delta_y


def _normalise_offset(delta: int, limit: int) -> float:
    if limit <= 0:
        return 0.0
    return delta / float(limit)


class Observation:
    """Encodes controller-facing features derived from the game state."""

    __slots__ = (
        "player",
        "players",
        "resources",
        "target",
        "monster",
        "_vector",
    )

    _VECTOR_LENGTH = 9

    def __init__(
        self,
        *,
        player: Player,
        players: Tuple[Player, ...],
        resources: Tuple[GridPosition, ...],
        target: GridPosition,
        monster: GridPosition,
    ) -> None:
        self.player = player
        self.players = players
        self.resources = resources
        self.target = target
        self.monster = monster
        self._vector = self._compute_vector()

    @classmethod
    def vector_length(cls) -> int:
        return cls._VECTOR_LENGTH

    def as_vector(self) -> Tuple[float, ...]:
        return self._vector

    def _compute_vector(self) -> Tuple[float, ...]:
        player_position = self.player.position
        width_span = max(1, FIELD_DIMENSIONS.width - 1)
        height_span = max(1, FIELD_DIMENSIONS.height - 1)

        resource_offset = self._nearest_resource_offset(player_position, width_span, height_span)
        target_offset = self._position_offset(self.target, player_position, width_span, height_span)
        nearest_player_offset = self._nearest_player_offset(player_position, width_span, height_span)
        monster_offset = self._position_offset(self.monster, player_position, width_span, height_span)
        has_resource = 1.0 if self.player.has_resource else 0.0

        return (
            resource_offset[0],
            resource_offset[1],
            target_offset[0],
            target_offset[1],
            nearest_player_offset[0],
            nearest_player_offset[1],
            monster_offset[0],
            monster_offset[1],
            has_resource,
        )

    def _nearest_resource_offset(
        self,
        player_position: GridPosition,
        width_span: int,
        height_span: int,
    ) -> Tuple[float, float]:
        nearest = self._nearest_position(player_position, self.resources)
        if nearest is None:
            return (0.0, 0.0)
        return self._position_offset(nearest, player_position, width_span, height_span)

    def _nearest_player_offset(
        self,
        player_position: GridPosition,
        width_span: int,
        height_span: int,
    ) -> Tuple[float, float]:
        others = tuple(player for player in self.players if player.identifier != self.player.identifier)
        candidates = tuple(player.position for player in others)
        nearest = self._nearest_position(player_position, candidates)
        if nearest is None:
            return (0.0, 0.0)
        return self._position_offset(nearest, player_position, width_span, height_span)

    def _nearest_position(
        self,
        origin: GridPosition,
        positions: Iterable[GridPosition],
    ) -> Optional[GridPosition]:
        candidates = list(positions)
        if not candidates:
            return None
        return min(candidates, key=lambda position: _distance_squared(origin, position))

    def _position_offset(
        self,
        position: GridPosition,
        origin: GridPosition,
        width_span: int,
        height_span: int,
    ) -> Tuple[float, float]:
        delta_x = position[0] - origin[0]
        delta_y = position[1] - origin[1]
        return (
            _normalise_offset(delta_x, width_span),
            _normalise_offset(delta_y, height_span),
        )

